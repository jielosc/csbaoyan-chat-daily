from __future__ import annotations

import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

from chat_processing import ChatChunk


EXTRACTION_SYSTEM_PROMPT = """你是一名熟悉“保研/夏令营/预推免/联系导师/实验室招生”语境的信息编辑。

你的任务是从一段群聊中提取真正有价值的信息，并忽略灌水、纯表情、无意义接龙和重复内容。

请重点提取：
1. 招生、夏令营、预推免、导师联系、考核、面试、机试、报名时间等信息。
2. 对学校、实验室、导师、方向、barrier、rank、流程、体验的有效讨论。
3. 群友总结出的经验、建议、避坑点。
4. 明显有趣且值得日报记录的讨论片段。

输出要求：
1. 使用 Markdown。
2. 先给“信息要点”，再给“有趣讨论（如有）”。
3. 每条尽量简洁，避免复述原文。
4. 不要输出邮箱、手机号、QQ、微信、个人主页、具体链接等联系方式。
5. 对明显带有主观色彩的负面评价，尽量改写为中性、克制的风险提示。
6. 对无法核实的传闻显式标注“待核实”。
7. 若本 Chunk 基本无有效信息，请明确写“本 Chunk 无值得记录的信息”。"""

FINAL_REPORT_SYSTEM_PROMPT = """你是一名“保研信息日报”编辑，负责把多段提取结果整理成一篇清晰、克制、可读的日报。

请根据用户提供的输出模板和分块提取内容生成最终日报，要求：
1. 优先保留对保研相关决策有帮助的信息。
2. 合并重复信息，去掉噪声和相互矛盾但无定论的表述。
3. 对明显不确定的内容加上“待进一步核实”等提示。
4. 若某一部分信息不足，请明确写“暂无值得记录的信息”。
5. 全文使用 Markdown，语言简洁自然，不要暴露匿名化前的隐私信息。
6. 不要输出邮箱、手机号、QQ、微信、具体网页链接或其他联系方式。
7. 对导师、实验室、学校的评价保持中性，不要使用“避雷”“坑”“黑奴”等强烈标签；如必须表达风险，用“存在争议”“需自行核实”“有较强负面反馈”等克制说法。
8. 明确区分“公开可验证信息”和“群聊经验/传闻”，传闻统一放到“风险与待核实”部分。"""


def create_openai_client(api_key: str | None, base_url: str | None, timeout: float):
    if not api_key:
        raise ValueError("缺少 OpenAI API Key。请设置 OPENAI_API_KEY 或通过 --api-key 传入。")

    try:
        from openai import OpenAI
    except ImportError as exc:
        raise ImportError("未安装 openai 库，请先执行 `pip install -r requirements.txt`。") from exc

    client_kwargs: dict[str, Any] = {"api_key": api_key, "timeout": timeout}
    if base_url:
        client_kwargs["base_url"] = base_url
    return OpenAI(**client_kwargs)


def call_llm_with_retry(
    client: Any,
    model: str,
    system_prompt: str,
    user_prompt: str,
    retries: int,
    temperature: float,
) -> str:
    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            response = client.chat.completions.create(
                model=model,
                temperature=temperature,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
            return response.choices[0].message.content.strip()
        except Exception as exc:
            last_error = exc
            logging.warning("LLM 调用失败，第 %s/%s 次重试：%s", attempt, retries, exc)
            if attempt < retries:
                time.sleep(min(2 ** attempt, 8))

    raise RuntimeError(f"LLM 调用最终失败：{last_error}") from last_error

def summarize_chunk(
    chunk: ChatChunk,
    client: Any,
    model: str,
    retries: int,
    temperature: float,
) -> tuple[int, str, str, str]:
    logging.info("处理 Chunk %s，时间范围 %s -> %s", chunk.index, chunk.start_time, chunk.end_time)
    user_prompt = (
        f"以下是一个 QQ 保研群聊 Chunk，请提取值得写入日报的信息。\n\n"
        f"Chunk 编号：{chunk.index}\n"
        f"时间范围：{chunk.start_time} - {chunk.end_time}\n\n"
        f"聊天内容：\n{chunk.text}"
    )
    chunk_summary = call_llm_with_retry(
        client=client,
        model=model,
        system_prompt=EXTRACTION_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        retries=retries,
        temperature=temperature,
    )
    return chunk.index, chunk.start_time, chunk.end_time, chunk_summary.strip()


def extract_all_chunks(
    chunks: list[ChatChunk],
    extracted_path: Path,
    client: Any,
    model: str,
    retries: int,
    temperature: float,
    max_workers: int,
) -> None:
    results: list[tuple[int, str, str, str]] = []

    if max_workers <= 1 or len(chunks) <= 1:
        for chunk in chunks:
            results.append(
                summarize_chunk(
                    chunk=chunk,
                    client=client,
                    model=model,
                    retries=retries,
                    temperature=temperature,
                )
            )
    else:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(
                    summarize_chunk,
                    chunk,
                    client,
                    model,
                    retries,
                    temperature,
                ): chunk.index
                for chunk in chunks
            }
            for future in as_completed(futures):
                results.append(future.result())

    results.sort(key=lambda item: item[0])

    with extracted_path.open("w", encoding="utf-8") as handle:
        for chunk_index, start_time, end_time, summary in results:
            handle.write(f"# Chunk {chunk_index}\n\n")
            handle.write(f"- 时间范围：{start_time} - {end_time}\n\n")
            handle.write(summary)
            handle.write("\n\n")

def generate_final_report(
    extracted_path: Path,
    final_report_path: Path,
    client: Any,
    model: str,
    retries: int,
    temperature: float,
) -> None:
    extracted_text = extracted_path.read_text(encoding="utf-8").strip()
    if not extracted_text:
        raise ValueError("extracted_info.md 为空，无法生成最终日报。")

    user_prompt = (
        f"请将下面的分块提取结果整理成最终《CS保研信息日报》。\n\n"
        f"请严格按以下 Markdown 模板输出，除内容外不要增加额外字段。\n\n"
        f"# CS保研信息日报\n\n"
        f"> 免责声明：以下内容来自群聊整理与公开信息交叉归纳，仅供参考，请以官方通知和公开资料为准。\n\n"
        f"## 今日概览\n\n"
        f"## 重要信息\n\n"
        f"## 经验/观点\n\n"
        f"## 有趣讨论\n\n"
        f"## 风险与待核实\n\n"
        f"分块提取内容：\n{extracted_text}"
    )
    report = call_llm_with_retry(
        client=client,
        model=model,
        system_prompt=FINAL_REPORT_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        retries=retries,
        temperature=temperature,
    )

    final_report_path.write_text(report.strip() + "\n", encoding="utf-8")
