from __future__ import annotations

import os
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

if load_dotenv is not None:
    load_dotenv()

# Local paths
EXPORT_DIR = Path(os.getenv("CSBAOYAN_EXPORT_DIR", "chat_exports"))
PAGES_DIR = Path(os.getenv("CSBAOYAN_PAGES_DIR", "pages"))

# Model provider config
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL")
