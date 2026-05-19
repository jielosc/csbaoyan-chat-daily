from __future__ import annotations

import datetime as dt
import logging
from pathlib import Path

from ..config import PAGES_DIR, SITE_BASE_URL, TELEGRAM_BOT_TOKEN, TELEGRAM_CHANNEL_ID, resolve_path
from ..domain.file_utils import validate_report_date
from ..infra.telegram import compose_message, extract_overview, read_report, resolve_report_path, send_telegram_message


def default_report_date() -> str:
    return (dt.date.today() - dt.timedelta(days=1)).strftime("%Y-%m-%d")


def resolve_broadcast_config(
    *,
    bot_token: str | None = None,
    channel_id: str | None = None,
    site_base_url: str | None = None,
) -> tuple[str, str, str] | None:
    required = {
        "TELEGRAM_BOT_TOKEN": bot_token if bot_token is not None else TELEGRAM_BOT_TOKEN,
        "TELEGRAM_CHANNEL_ID": channel_id if channel_id is not None else TELEGRAM_CHANNEL_ID,
        "SITE_BASE_URL": site_base_url if site_base_url is not None else SITE_BASE_URL,
    }
    missing = [name for name, value in required.items() if not str(value or "").strip()]
    if missing:
        logging.warning("Skipping Telegram broadcast: missing required config: %s", ", ".join(missing))
        return None

    return (
        str(required["TELEGRAM_BOT_TOKEN"]).strip(),
        str(required["TELEGRAM_CHANNEL_ID"]).strip(),
        str(required["SITE_BASE_URL"]).strip(),
    )


def broadcast_report(
    *,
    report_date: str | None = None,
    pages_dir: Path = PAGES_DIR,
    bot_token: str | None = None,
    channel_id: str | None = None,
    site_base_url: str | None = None,
) -> bool:
    config = resolve_broadcast_config(bot_token=bot_token, channel_id=channel_id, site_base_url=site_base_url)
    if config is None:
        return False

    resolved_report_date = validate_report_date(report_date) if report_date else default_report_date()
    resolved_pages_dir = resolve_path(pages_dir)
    resolved_bot_token, resolved_channel_id, resolved_site_base_url = config

    report_path = resolve_report_path(resolved_pages_dir, resolved_report_date)
    report_markdown = read_report(report_path)
    overview = extract_overview(report_markdown)
    message = compose_message(resolved_report_date, overview, resolved_site_base_url)
    send_telegram_message(resolved_bot_token, resolved_channel_id, message)
    logging.info("Telegram broadcast sent for %s", resolved_report_date)
    return True

