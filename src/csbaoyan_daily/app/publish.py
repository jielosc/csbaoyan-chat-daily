from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..infra.git_publish import (
    PublishResult,
    assert_git_origin,
    assert_upstream_synced,
    get_current_branch,
    publish_pathspec,
)


@dataclass(frozen=True)
class PublishOptions:
    repo_root: Path
    push: bool = True
    pathspec: str = "pages/data"
    commit_message: str = "chore: update pages data"


def run_publish_preflight(repo_root: Path) -> str:
    resolved_repo_root = repo_root.resolve()
    assert_git_origin(resolved_repo_root)
    branch = get_current_branch(resolved_repo_root)
    assert_upstream_synced(resolved_repo_root, branch, "preflight")
    return branch


def run_publish(options: PublishOptions) -> PublishResult:
    return publish_pathspec(
        repo_root=options.repo_root.resolve(),
        pathspec=options.pathspec,
        commit_message=options.commit_message,
        push=options.push,
    )

