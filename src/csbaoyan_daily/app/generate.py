from __future__ import annotations

import datetime as dt
import logging
from dataclasses import dataclass
from pathlib import Path

from ..config import EXPORT_DIR, OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL, PAGES_DIR, resolve_path
from ..domain.chat_processing import anonymize_messages, chunk_messages, write_anonymized_transcript
from ..domain.file_utils import (
    extract_messages,
    get_json_file_by_date,
    infer_report_date,
    load_chat_export,
    prepare_output_paths,
    validate_report_date,
    write_reports_manifest,
)
from ..domain.report_generation import extract_all_chunks, generate_final_report
from ..infra.openai_client import create_openai_client


@dataclass(frozen=True)
class GenerateOptions:
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


@dataclass(frozen=True)
class GenerateArtifacts:
    report_date: str
    export_file: Path
    extracted_path: Path
    report_path: Path
    transcript_path: Path
    manifest_count: int
    message_count: int
    chunk_count: int


def default_report_date() -> str:
    return (dt.date.today() - dt.timedelta(days=1)).strftime("%Y-%m-%d")


def run_generate_report(options: GenerateOptions) -> GenerateArtifacts:
    target_date = validate_report_date(options.date) if options.date else default_report_date()
    export_dir = resolve_path(options.export_dir)
    pages_dir = resolve_path(options.pages_dir)

    export_file = get_json_file_by_date(export_dir, target_date)
    payload = load_chat_export(export_file)
    messages = extract_messages(payload)
    anonymized_messages = anonymize_messages(messages)
    chunks = chunk_messages(
        anonymized_messages,
        max_chars=options.chunk_max_chars,
        max_messages=options.chunk_max_messages,
        overlap_messages=options.chunk_overlap_messages,
    )

    inferred_report_date = infer_report_date(payload, export_file)
    report_date = validate_report_date(options.date) if options.date else inferred_report_date
    extracted_path, report_path, transcript_path = prepare_output_paths(pages_dir, report_date)
    write_anonymized_transcript(anonymized_messages, transcript_path)

    extraction_client = create_openai_client(options.api_key, options.base_url, options.timeout)
    final_client = create_openai_client(options.api_key, options.base_url, options.final_timeout)

    logging.info("使用日期 %s 的导出文件：%s", target_date, export_file)
    if inferred_report_date != target_date:
        logging.warning("目标日期为 %s，但导出内容推断日期为 %s，将按目标日期输出。", target_date, inferred_report_date)
    logging.info("脱敏后消息数：%s，Chunk 数：%s", len(anonymized_messages), len(chunks))
    logging.info("LLM 超时设置：分块提取 %ss，最终汇总 %ss", options.timeout, options.final_timeout)

    extract_all_chunks(
        chunks=chunks,
        extracted_path=extracted_path,
        client=extraction_client,
        model=options.model or OPENAI_MODEL,
        retries=options.retries,
        temperature=options.temperature,
        max_workers=options.max_workers,
    )

    generate_final_report(
        extracted_path=extracted_path,
        final_report_path=report_path,
        client=final_client,
        model=options.model or OPENAI_MODEL,
        retries=options.retries,
        temperature=options.temperature,
    )

    manifest = write_reports_manifest(pages_dir)

    logging.info("中间提取结果：%s", extracted_path)
    logging.info("脱敏聊天记录：%s", transcript_path)
    logging.info("最终日报：%s", report_path)
    logging.info("站点索引已刷新，共 %s 篇日报", len(manifest))

    return GenerateArtifacts(
        report_date=report_date,
        export_file=export_file,
        extracted_path=extracted_path,
        report_path=report_path,
        transcript_path=transcript_path,
        manifest_count=len(manifest),
        message_count=len(anonymized_messages),
        chunk_count=len(chunks),
    )

