from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class UpstreamStatus:
    has_upstream: bool
    ahead: int = 0
    behind: int = 0


@dataclass(frozen=True)
class PublishResult:
    changes_detected: bool
    committed: bool
    pushed: bool
    branch: str | None = None


def _run_git(repo_root: Path, *args: str, capture_output: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=repo_root,
        text=True,
        capture_output=capture_output,
        check=False,
    )


def _invoke_git(repo_root: Path, error_message: str, *args: str) -> subprocess.CompletedProcess[str]:
    result = _run_git(repo_root, *args)
    if result.returncode != 0:
        raise RuntimeError(error_message)
    return result


def assert_git_origin(repo_root: Path) -> None:
    if _run_git(repo_root, "remote", "get-url", "origin").returncode != 0:
        raise RuntimeError("Git remote origin is not configured. Run: git remote add origin <your-github-repo-url>")


def get_current_branch(repo_root: Path) -> str:
    result = _run_git(repo_root, "branch", "--show-current", capture_output=True)
    branch = result.stdout.strip() if result.returncode == 0 else ""
    if not branch:
        raise RuntimeError("Could not detect the current branch. Check out a local branch first.")
    return branch


def test_working_tree_clean(repo_root: Path) -> bool:
    result = _run_git(repo_root, "status", "--porcelain", capture_output=True)
    return result.returncode == 0 and not result.stdout.strip()


def get_upstream_status(repo_root: Path, branch: str) -> UpstreamStatus:
    has_upstream = _run_git(
        repo_root,
        "rev-parse",
        "--abbrev-ref",
        "--symbolic-full-name",
        "@{u}",
    ).returncode == 0
    if not has_upstream:
        return UpstreamStatus(has_upstream=False)

    _invoke_git(repo_root, "git fetch failed.", "fetch", "origin", branch)
    result = _run_git(repo_root, "rev-list", "--left-right", "--count", f"HEAD...origin/{branch}", capture_output=True)
    counts = result.stdout.strip()
    if result.returncode != 0 or not counts:
        raise RuntimeError(f"Could not determine branch divergence against origin/{branch}.")

    parts = counts.split()
    if len(parts) < 2:
        raise RuntimeError(f"Unexpected git rev-list output: {counts}")

    return UpstreamStatus(has_upstream=True, ahead=int(parts[0]), behind=int(parts[1]))


def sync_upstream_if_behind(repo_root: Path, branch: str, phase: str) -> UpstreamStatus:
    status = get_upstream_status(repo_root, branch)
    if not status.has_upstream or status.behind <= 0:
        return status

    if status.ahead > 0:
        raise RuntimeError(
            f"Local branch diverged from origin/{branch} during {phase} "
            f"(ahead={status.ahead}, behind={status.behind}). Resolve it manually before running the daily pipeline."
        )

    if not test_working_tree_clean(repo_root):
        raise RuntimeError(
            f"Local branch is behind origin/{branch} during {phase}, but the working tree is not clean. "
            "Commit or stash local changes, then rerun the daily pipeline."
        )

    _invoke_git(repo_root, "git pull --ff-only failed.", "pull", "--ff-only", "origin", branch)
    return get_upstream_status(repo_root, branch)


def assert_upstream_synced(repo_root: Path, branch: str, phase: str, allow_ahead: bool = False) -> None:
    status = sync_upstream_if_behind(repo_root, branch, phase)
    if not status.has_upstream:
        return

    has_blocking_ahead = not allow_ahead and status.ahead > 0
    if has_blocking_ahead or status.behind > 0:
        raise RuntimeError(
            f"Local branch is not in sync with origin/{branch} during {phase} "
            f"(ahead={status.ahead}, behind={status.behind}). Resolve it manually before running the daily pipeline."
        )


def stage_pathspec(repo_root: Path, pathspec: str) -> None:
    _invoke_git(repo_root, f"git add {pathspec} failed.", "add", "--all", "--", pathspec)


def has_pending_pathspec_changes(repo_root: Path, pathspec: str) -> bool:
    result = _run_git(repo_root, "status", "--porcelain", "--", pathspec, capture_output=True)
    return result.returncode == 0 and bool(result.stdout.strip())


def commit_pathspec(repo_root: Path, pathspec: str, commit_message: str) -> None:
    _invoke_git(repo_root, "git commit failed.", "commit", "-m", commit_message, "--", pathspec)


def push_branch(repo_root: Path, branch: str) -> None:
    status = get_upstream_status(repo_root, branch)
    if status.has_upstream:
        _invoke_git(repo_root, "git push failed.", "push")
    else:
        _invoke_git(repo_root, "git push failed.", "push", "-u", "origin", branch)


def publish_pathspec(
    repo_root: Path,
    pathspec: str = "pages/data",
    commit_message: str = "chore: update pages data",
    push: bool = True,
) -> PublishResult:
    stage_pathspec(repo_root, pathspec)
    if not has_pending_pathspec_changes(repo_root, pathspec):
        return PublishResult(changes_detected=False, committed=False, pushed=False)

    commit_pathspec(repo_root, pathspec, commit_message)
    if not push:
        return PublishResult(changes_detected=True, committed=True, pushed=False)

    assert_git_origin(repo_root)
    branch = get_current_branch(repo_root)
    assert_upstream_synced(repo_root, branch, "pre-push", allow_ahead=True)
    push_branch(repo_root, branch)
    return PublishResult(changes_detected=True, committed=True, pushed=True, branch=branch)

