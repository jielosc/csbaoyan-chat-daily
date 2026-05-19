from __future__ import annotations

import re
import subprocess
from pathlib import Path

from ..config import PAGES_DIR, resolve_path

EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
URL_PATTERN = re.compile(
    r"(?i)\b(?:https?://|www\.)[^\s]+|(?<!@)\b(?:[A-Za-z0-9-]+\.)+(?:com|cn|edu|org|net|io|ai|cc)(?:/[^\s]*)?"
)
PHONE_PATTERN = re.compile(r"(?<!\d)(?:\+?86[- ]?)?1[3-9]\d{9}(?!\d)")
CONTACT_ID_PATTERN = re.compile(r"(?i)\b(?:qq|vx|wechat|weixin|微信)[:： ]*[A-Za-z0-9_-]{5,}\b")
CORRUPTED_ALIAS_PATTERN = re.compile(r"User_\d+(?:学院|实验室|学校|大学|系|中心|研究院|平台)")
RISKY_WORD_PATTERN = re.compile(r"避雷|坑导|黑奴|高压|恶心|压榨")


def scan_text(path: Path, text: str, repo_root: Path) -> list[str]:
    issues: list[str] = []
    checks = [
        (EMAIL_PATTERN, "contains an email address"),
        (URL_PATTERN, "contains a URL or homepage"),
        (PHONE_PATTERN, "contains a phone number"),
        (CONTACT_ID_PATTERN, "contains a QQ/WeChat style contact"),
        (CORRUPTED_ALIAS_PATTERN, "contains a corrupted anonymization token"),
        (RISKY_WORD_PATTERN, "contains a high-risk negative label"),
    ]
    for pattern, label in checks:
        match = pattern.search(text)
        if match:
            issues.append(f"{path.relative_to(repo_root)}: {label}: {match.group(0)}")
    return issues


def _list_tracked_files(repo_root: Path, pathspec: str) -> list[str]:
    try:
        result = subprocess.run(
            ["git", "ls-files", pathspec],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return []
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def format_release_issues(issues: list[str]) -> str:
    lines = ["Release check failed:"]
    lines.extend(f"- {issue}" for issue in issues)
    return "\n".join(lines)


def run_release_check(repo_root: Path, pages_dir: Path = PAGES_DIR) -> list[str]:
    resolved_repo_root = repo_root.resolve()
    public_reports_dir = resolve_path(pages_dir, resolved_repo_root) / "data" / "reports"
    issues: list[str] = []

    tracked_public_extracted = _list_tracked_files(resolved_repo_root, "pages/data/extracted")
    if tracked_public_extracted:
        issues.append("pages/data/extracted still has tracked public intermediate files")

    tracked_transcripts = _list_tracked_files(resolved_repo_root, "internal/transcripts")
    if tracked_transcripts:
        issues.append("internal/transcripts still has tracked internal transcript files")

    if public_reports_dir.exists():
        for path in sorted(public_reports_dir.glob("*.md")):
            issues.extend(scan_text(path, path.read_text(encoding="utf-8"), resolved_repo_root))

    return issues
