from __future__ import annotations

import datetime as dt
import json
import re
import time
from pathlib import Path
from typing import Any


DATE_PATTERN = re.compile(r"(\d{4}-\d{2}-\d{2})T")
REPORT_FILE_PATTERN = re.compile(r"^(\d{4}-\d{2}-\d{2})\.md$")
MANIFEST_FILENAME = "reports.json"


def validate_report_date(value: str) -> str:
    try:
        return dt.datetime.strptime(value, "%Y-%m-%d").strftime("%Y-%m-%d")
    except ValueError as exc:
        raise ValueError(f"日期格式无效：{value}，请使用 YYYY-MM-DD。") from exc


def _list_json_files(export_dir: Path) -> list[Path]:
    if not export_dir.exists():
        raise FileNotFoundError(f"导出目录不存在：{export_dir}")

    json_files = [path for path in export_dir.glob("*.json") if path.is_file()]
    if not json_files:
        raise FileNotFoundError(f"导出目录中没有 JSON 文件：{export_dir}")
    return json_files


def _extract_date_from_filename(export_file: Path) -> str | None:
    match = DATE_PATTERN.search(export_file.stem)
    return match.group(1) if match else None


def _describe_available_dates(json_files: list[Path]) -> str:
    dates = sorted({date for path in json_files if (date := _extract_date_from_filename(path))}, reverse=True)
    if not dates:
        return "目录中的文件名未包含可识别日期。"
    preview = ", ".join(dates[:10])
    if len(dates) > 10:
        preview = f"{preview} 等 {len(dates)} 个日期"
    return f"可用日期：{preview}"


def get_latest_json_file(export_dir: Path) -> Path:
    json_files = _list_json_files(export_dir)
    return max(json_files, key=lambda path: path.stat().st_mtime)


def get_json_file_by_date(export_dir: Path, report_date: str) -> Path:
    normalized_date = validate_report_date(report_date)
    json_files = _list_json_files(export_dir)
    matched_files = [path for path in json_files if _extract_date_from_filename(path) == normalized_date]
    if matched_files:
        return max(matched_files, key=lambda path: path.stat().st_mtime)

    payload_matched_files: list[Path] = []
    for path in json_files:
        try:
            payload = load_chat_export(path)
        except ValueError:
            continue
        if infer_report_date(payload, path) == normalized_date:
            payload_matched_files.append(path)
    if payload_matched_files:
        return max(payload_matched_files, key=lambda path: path.stat().st_mtime)

    raise FileNotFoundError(f"未找到日期为 {normalized_date} 的导出文件。{_describe_available_dates(json_files)}")


def load_chat_export(file_path: Path) -> dict[str, Any]:
    try:
        return json.loads(file_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"JSON 解析失败：{file_path}") from exc


def extract_messages(payload: dict[str, Any]) -> list[dict[str, Any]]:
    messages = payload.get("messages")
    if not isinstance(messages, list):
        raise ValueError("JSON 中缺少 messages 列表。")
    return messages


def infer_report_date(payload: dict[str, Any], export_file: Path) -> str:
    statistics = payload.get("statistics") or {}
    time_range = statistics.get("timeRange") or {}
    end_value = str(time_range.get("end") or "").strip()
    if end_value:
        return end_value[:10]

    file_date = _extract_date_from_filename(export_file)
    if file_date:
        return file_date
    return time.strftime("%Y-%m-%d")


def prepare_output_paths(pages_dir: Path, report_date: str) -> tuple[Path, Path, Path]:
    pages_data_dir = pages_dir / "data"
    extracted_dir = pages_dir.parent / "internal" / "extracted"
    reports_dir = pages_data_dir / "reports"
    transcripts_dir = pages_dir.parent / "internal" / "transcripts"
    extracted_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)
    transcripts_dir.mkdir(parents=True, exist_ok=True)
    extracted_path = extracted_dir / f"{report_date}.md"
    report_path = reports_dir / f"{report_date}.md"
    transcript_path = transcripts_dir / f"{report_date}.txt"
    return extracted_path, report_path, transcript_path


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


def write_reports_manifest(pages_dir: Path) -> list[dict[str, str]]:
    data_dir = pages_dir / "data"
    reports_dir = data_dir / "reports"
    data_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)

    manifest: list[dict[str, str]] = []
    for report_date, report_path in _iter_report_paths(reports_dir):
        if not report_path.read_text(encoding="utf-8").strip():
            continue
        manifest.append(
            {
                "date": report_date,
                "md_path": f"reports/{report_path.name}",
            }
        )

    manifest_path = data_dir / MANIFEST_FILENAME
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest
