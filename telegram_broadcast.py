from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import logging
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

from app_config import PAGES_DIR, SITE_BASE_URL, TELEGRAM_BOT_TOKEN, TELEGRAM_CHANNEL_ID
from file_utils import validate_report_date


OVERVIEW_SECTION_PATTERN = re.compile(r"##\s*今日概览\s*\n+([\s\S]*?)(?=\n##\s|$)")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Broadcast the daily report overview to a Telegram channel.")
    parser.add_argument(
        "--date",
        type=validate_report_date,
        default=(dt.date.today() - dt.timedelta(days=1)).strftime("%Y-%m-%d"),
        help="Report date in YYYY-MM-DD format.",
    )
    parser.add_argument(
        "--pages-dir",
        type=Path,
        default=PAGES_DIR,
        help="Pages directory that contains data/reports.",
    )
    return parser.parse_args()


def extract_overview(markdown_text: str) -> str:
    match = OVERVIEW_SECTION_PATTERN.search(markdown_text)
    if not match:
        raise ValueError("日报中缺少“今日概览”章节。")

    lines = match.group(1).splitlines()
    for raw_line in lines:
        line = raw_line.strip()
        if not line or line.startswith(">"):
            continue
        line = re.sub(r"^([-+*]|\d+[.)])\s+", "", line)
        line = re.sub(r"[`*_#]+", "", line)
        if line:
            return line

    raise ValueError("“今日概览”章节为空，无法构造 Telegram 播报。")


def build_report_url(site_base_url: str, report_date: str) -> str:
    normalized = site_base_url.strip().rstrip("/")
    if not normalized:
        raise ValueError("SITE_BASE_URL 不能为空。")
    return f"{normalized}/#{report_date}"


def compose_message(report_date: str, overview: str, site_base_url: str) -> str:
    escaped_overview = html.escape(overview, quote=True)
    report_url = html.escape(build_report_url(site_base_url, report_date), quote=True)
    return (
        f"{escaped_overview}\n\n"
        f'<a href="{report_url}">阅读全文</a>'
    )


def resolve_report_path(pages_dir: Path, report_date: str) -> Path:
    return pages_dir / "data" / "reports" / f"{report_date}.md"


def read_report(report_path: Path) -> str:
    if not report_path.exists():
        raise FileNotFoundError(f"日报文件不存在：{report_path}")
    return report_path.read_text(encoding="utf-8")


def send_telegram_message(bot_token: str, channel_id: str, message: str) -> None:
    request_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = json.dumps(
        {
            "chat_id": channel_id,
            "text": message,
            "parse_mode": "HTML",
            "disable_web_page_preview": False,
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        request_url,
        data=payload,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            response_payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        response_text = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Telegram API HTTP {exc.code}: {response_text}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Telegram API request failed: {exc.reason}") from exc

    if not response_payload.get("ok"):
        raise RuntimeError(f"Telegram API returned an error: {response_payload}")


def get_required_config() -> tuple[str, str, str] | None:
    required = {
        "TELEGRAM_BOT_TOKEN": TELEGRAM_BOT_TOKEN,
        "TELEGRAM_CHANNEL_ID": TELEGRAM_CHANNEL_ID,
        "SITE_BASE_URL": SITE_BASE_URL,
    }
    missing = [name for name, value in required.items() if not str(value or "").strip()]
    if missing:
        logging.warning("Skipping Telegram broadcast: missing required config: %s", ", ".join(missing))
        return None

    return (
        str(TELEGRAM_BOT_TOKEN).strip(),
        str(TELEGRAM_CHANNEL_ID).strip(),
        str(SITE_BASE_URL).strip(),
    )


def main() -> int:
    args = parse_args()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        stream=sys.stdout,
    )

    config = get_required_config()
    if config is None:
        return 0

    bot_token, channel_id, site_base_url = config

    try:
        report_path = resolve_report_path(args.pages_dir, args.date)
        report_markdown = read_report(report_path)
        overview = extract_overview(report_markdown)
        message = compose_message(args.date, overview, site_base_url)
        send_telegram_message(bot_token, channel_id, message)
        logging.info("Telegram broadcast sent for %s", args.date)
        return 0
    except Exception as exc:
        logging.error("Telegram broadcast failed: %s", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
