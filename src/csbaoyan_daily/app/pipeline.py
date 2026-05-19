from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from ..config import EXPORT_DIR, OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL, PAGES_DIR
from ..domain.file_utils import validate_report_date
from .broadcast import broadcast_report, default_report_date
from .generate import GenerateOptions, run_generate_report
from .publish import PublishOptions, run_publish, run_publish_preflight
from .verify import format_release_issues, run_release_check


@dataclass(frozen=True)
class PipelineOptions:
    repo_root: Path
    export_dir: Path = EXPORT_DIR
    pages_dir: Path = PAGES_DIR
    date: str | None = None
    model: str | None = OPENAI_MODEL
    chunk_max_chars: int = 30000
    chunk_max_messages: int = 600
    chunk_overlap_messages: int = 30
    retries: int = 3
    timeout: float = 120.0
    final_timeout: float = 300.0
    temperature: float = 0.2
    max_workers: int = 4
    base_url: str | None = OPENAI_BASE_URL
    api_key: str | None = OPENAI_API_KEY
    skip_generate: bool = False
    skip_release_check: bool = False
    skip_commit: bool = False
    skip_push: bool = False
    skip_telegram: bool = False


def _resolved_report_date(report_date: str | None) -> str:
    return validate_report_date(report_date) if report_date else default_report_date()


def run_pipeline(options: PipelineOptions) -> str:
    repo_root = options.repo_root.resolve()
    report_date = _resolved_report_date(options.date)

    if not options.skip_commit and not options.skip_push:
        logging.info("Checking Git remote and upstream before generation")
        run_publish_preflight(repo_root)

    if not options.skip_generate:
        logging.info("Running generate phase")
        artifacts = run_generate_report(
            GenerateOptions(
                export_dir=options.export_dir,
                pages_dir=options.pages_dir,
                date=options.date,
                model=options.model,
                chunk_max_chars=options.chunk_max_chars,
                chunk_max_messages=options.chunk_max_messages,
                chunk_overlap_messages=options.chunk_overlap_messages,
                retries=options.retries,
                timeout=options.timeout,
                final_timeout=options.final_timeout,
                temperature=options.temperature,
                max_workers=options.max_workers,
                base_url=options.base_url,
                api_key=options.api_key,
            )
        )
        report_date = artifacts.report_date

    if not options.skip_release_check:
        logging.info("Running release check")
        issues = run_release_check(repo_root=repo_root, pages_dir=options.pages_dir)
        if issues:
            raise RuntimeError(format_release_issues(issues))
        logging.info("Release check passed.")

    if options.skip_commit:
        logging.info("Skipping all git operations as requested.")
        logging.info("Skipping Telegram broadcast because git operations were skipped.")
        logging.info("Daily pipeline completed.")
        return report_date

    publish_result = run_publish(
        PublishOptions(
            repo_root=repo_root,
            push=not options.skip_push,
        )
    )

    if not publish_result.changes_detected:
        logging.info("No changes detected in pages/data. Nothing to commit or push.")
        logging.info("Skipping Telegram broadcast because no publishable changes were produced.")
        logging.info("Daily pipeline completed.")
        return report_date

    if options.skip_push:
        logging.info("Skipping git push as requested.")
        logging.info("Skipping Telegram broadcast because git push was skipped.")
        logging.info("Daily pipeline completed.")
        return report_date

    if options.skip_telegram:
        logging.info("Skipping Telegram broadcast as requested.")
        logging.info("Daily pipeline completed.")
        return report_date

    try:
        logging.info("Sending Telegram broadcast")
        broadcast_report(report_date=report_date, pages_dir=options.pages_dir)
    except Exception as exc:
        logging.warning("Telegram broadcast failed but the daily pipeline will continue: %s", exc)

    logging.info("Daily pipeline completed.")
    return report_date

