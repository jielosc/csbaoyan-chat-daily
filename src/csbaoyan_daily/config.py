from __future__ import annotations

import os
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

REPO_ROOT = Path(__file__).resolve().parents[2]

if load_dotenv is not None:
    load_dotenv(REPO_ROOT / ".env")

# Local paths
EXPORT_DIR = Path(os.getenv("CSBAOYAN_EXPORT_DIR", "chat_exports"))
PAGES_DIR = Path(os.getenv("CSBAOYAN_PAGES_DIR", "pages"))

# Model provider config
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL")

# Telegram broadcast config
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID")
SITE_BASE_URL = os.getenv("SITE_BASE_URL")


def resolve_path(path: Path, base: Path | None = None) -> Path:
    if path.is_absolute():
        return path
    return (base or REPO_ROOT) / path
