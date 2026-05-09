"""DeepSeek model client built on LangChain.
基于 LangChain 的 DeepSeek 模型客户端。
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from ..core import get_settings


@lru_cache(maxsize=1)
def deepseek_is_configured() -> bool:
    """Check whether the DeepSeek client has the minimum required settings.
    检查 DeepSeek 客户端是否具备最基本的配置。
    """

    settings = get_settings()
    return bool(settings.deepseek_api_key and settings.deepseek_base_url and settings.deepseek_model)


@lru_cache(maxsize=1)
def get_deepseek_chat_model() -> Any:
    """Build and cache a LangChain ChatOpenAI model backed by DeepSeek.
    构建并缓存一个基于 DeepSeek 的 LangChain ChatOpenAI 模型。
    """

    settings = get_settings()
    if not deepseek_is_configured():
        raise RuntimeError("DeepSeek is not configured")

    try:
        from langchain_openai import ChatOpenAI
    except ImportError as exc:
        raise RuntimeError("langchain-openai is required for DeepSeek requests") from exc

    return ChatOpenAI(
        model=settings.deepseek_model,
        api_key=settings.deepseek_api_key,
        base_url=settings.deepseek_base_url,
        # 意图识别希望输出稳定，所以这里把温度设低。
        temperature=0.7,
        timeout=settings.deepseek_timeout_seconds,
        max_retries=settings.deepseek_max_retries,
    )
