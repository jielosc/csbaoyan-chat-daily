from __future__ import annotations

import argparse
import datetime as dt
import logging
import sys
from pathlib import Path

from app_config import EXPORT_DIR, OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL, PAGES_DIR
from chat_processing import anonymize_messages, chunk_messages, write_anonymized_transcript
from file_utils import (
    extract_messages,
    get_json_file_by_date,
    infer_report_date,
    load_chat_export,
    prepare_output_paths,
    validate_report_date,
    write_reports_manifest,
)
from report_generation import create_openai_client, extract_all_chunks, generate_final_report


DEFAULT_EXPORT_DIR = EXPORT_DIR
DEFAULT_MODEL = OPENAI_MODEL
DEFAULT_BASE_URL = OPENAI_BASE_URL
DEFAULT_API_KEY = OPENAI_API_KEY


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a daily summary from a QQ chat export.")
    parser.add_argument("--export-dir", type=Path, default=DEFAULT_EXPORT_DIR, help="Directory containing exported QQ chat JSON files.")
    parser.add_argument("--date", type=validate_report_date, help="Target report date in YYYY-MM-DD format.")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="OpenAI-compatible model name.")
    parser.add_argument("--chunk-max-chars", type=int, default=30000, help="Maximum character count per chunk.")
    parser.add_argument("--chunk-max-messages", type=int, default=600, help="Maximum message count per chunk.")
    parser.add_argument("--chunk-overlap-messages", type=int, default=30, help="Number of overlapping messages between adjacent chunks.")
    parser.add_argument("--retries", type=int, default=3, help="Maximum retry count for failed LLM calls.")
    parser.add_argument("--timeout", type=float, default=120.0, help="LLM request timeout in seconds.")
    parser.add_argument("--final-timeout", type=float, default=300.0, help="Timeout in seconds for the final aggregation request.")
    parser.add_argument("--temperature", type=float, default=0.2, help="Sampling temperature for the LLM.")
    parser.add_argument("--max-workers", type=int, default=4, help="Worker count for chunk extraction.")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="Optional custom base URL for an OpenAI-compatible API.")
    parser.add_argument("--api-key", default=DEFAULT_API_KEY, help="Optional API key for the OpenAI-compatible API.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        stream=sys.stdout,
    )

    try:
        target_date = args.date or (dt.date.today() - dt.timedelta(days=1)).strftime("%Y-%m-%d")
        export_file = get_json_file_by_date(args.export_dir, target_date)
        payload = load_chat_export(export_file)
        messages = extract_messages(payload)
        anonymized_messages = anonymize_messages(messages)
        chunks = chunk_messages(
            anonymized_messages,
            max_chars=args.chunk_max_chars,
            max_messages=args.chunk_max_messages,
            overlap_messages=args.chunk_overlap_messages,
        )

        inferred_report_date = infer_report_date(payload, export_file)
        report_date = args.date or inferred_report_date
        extracted_path, report_path, transcript_path = prepare_output_paths(PAGES_DIR, report_date)
        write_anonymized_transcript(anonymized_messages, transcript_path)

        extraction_client = create_openai_client(args.api_key, args.base_url, args.timeout)
        final_client = create_openai_client(args.api_key, args.base_url, args.final_timeout)

        logging.info("使用日期 %s 的导出文件：%s", target_date, export_file)
        if inferred_report_date != target_date:
            logging.warning("目标日期为 %s，但导出内容推断日期为 %s，将按目标日期输出。", target_date, inferred_report_date)
        logging.info("脱敏后消息数：%s，Chunk 数：%s", len(anonymized_messages), len(chunks))
        logging.info("LLM 超时设置：分块提取 %ss，最终汇总 %ss", args.timeout, args.final_timeout)

        extract_all_chunks(
            chunks=chunks,
            extracted_path=extracted_path,
            client=extraction_client,
            model=args.model,
            retries=args.retries,
            temperature=args.temperature,
            max_workers=args.max_workers,
        )

        generate_final_report(
            extracted_path=extracted_path,
            final_report_path=report_path,
            client=final_client,
            model=args.model,
            retries=args.retries,
            temperature=args.temperature,
        )

        manifest = write_reports_manifest(PAGES_DIR)

        logging.info("中间提取结果：%s", extracted_path)
        logging.info("脱敏聊天记录：%s", transcript_path)
        logging.info("最终日报：%s", report_path)
        logging.info("站点索引已刷新，共 %s 篇日报", len(manifest))
        return 0
    except Exception as exc:
        logging.exception("生成日报失败：%s", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
