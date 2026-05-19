from __future__ import annotations

import html
import json
import re
import urllib.error
import urllib.request
from pathlib import Path

OVERVIEW_SECTION_PATTERN = re.compile(r"##\s*今日概览\s*\n+([\s\S]*?)(?=\n##\s|$)")


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
