from __future__ import annotations

from typing import Any


def create_openai_client(api_key: str | None, base_url: str | None, timeout: float) -> Any:
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

