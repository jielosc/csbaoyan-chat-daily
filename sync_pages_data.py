from __future__ import annotations

import json
import logging
import re
import sys
from pathlib import Path

from app_config import PAGES_DIR


MANIFEST_FILENAME = "reports.json"
REPORT_FILE_PATTERN = re.compile(r"^(\d{4}-\d{2}-\d{2})\.md$")


def _iter_report_paths(reports_dir: Path) -> list[tuple[str, Path]]:
    if not reports_dir.exists():
        return []

    report_paths: list[tuple[str, Path]] = []
    for path in reports_dir.iterdir():
        if not path.is_file():
            continue

        match = REPORT_FILE_PATTERN.fullmatch(path.name)
        if match:
            report_paths.append((match.group(1), path))

    return sorted(report_paths, key=lambda item: item[0], reverse=True)


def sync_pages_data(site_dir: Path = PAGES_DIR) -> list[dict[str, str]]:
    data_dir = site_dir / "data"
    reports_dir = data_dir / "reports"
    data_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)

    manifest: list[dict[str, str]] = []
    for report_date, report_path in _iter_report_paths(reports_dir):
        try:
            if not report_path.read_text(encoding="utf-8").strip():
                logging.warning("跳过空日报：%s", report_path)
                continue

            manifest.append(
                {
                    "date": report_date,
                    "md_path": f"reports/{report_path.name}",
                }
            )
        except Exception as exc:
            logging.warning("跳过损坏日报 %s：%s", report_path, exc)

    manifest_path = data_dir / MANIFEST_FILENAME
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    logging.info("日报站点已同步：%s（共 %s 篇）", manifest_path, len(manifest))
    return manifest


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    try:
        sync_pages_data()
        return 0
    except Exception as exc:
        logging.exception("同步日报站点数据失败：%s", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
