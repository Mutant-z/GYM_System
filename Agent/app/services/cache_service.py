"""Redis-backed cache helpers for RAG and chat flows.
用于 RAG 与聊天流程的 Redis 缓存工具。
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

from ..core import get_settings
from ..integrations.redis_client import get_redis_client

# 缓存版本号，当数据结构发生重大变化时修改此版本号以隔离旧数据
_CACHE_SCHEMA_VERSION = "v3"


def build_cache_key(*parts: str) -> str:
    """Build a safe cache key under the configured key prefix.
    根据应用配置的前缀构造标准化的 Redis 缓存键。
    """

    settings = get_settings()
    prefix = settings.redis_key_prefix or "agent"
    # 过滤掉空字符串并进行首尾去重
    normalized = [str(part).strip() for part in parts if str(part).strip()]
    # 拼接版本号和业务标识
    versioned = [f"schema_{_CACHE_SCHEMA_VERSION}", *normalized]
    return ":".join([prefix, *versioned]) if versioned else prefix


def stable_hash(payload: Any) -> str:
    """Build a stable hash string for cache partitioning.
    为对象生成稳定的哈希值，主要用于将复杂的 query 对象作为缓存键的一部分。
    """

    # 序列化时进行 Key 排序以确保相同内容生成的哈希值一致
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def get_cached_answer(*, query: str, collection: str) -> dict[str, Any] | None:
    """尝试从缓存中获取已有的 RAG 回答结果。"""
    settings = get_settings()
    key = build_cache_key("rag", "answer", collection, stable_hash({"q": query}))
    return _get_json(key, ttl_seconds=settings.redis_answer_ttl_seconds)


def set_cached_answer(*, query: str, collection: str, payload: dict[str, Any]) -> None:
    """将生成的 RAG 回答结果存入缓存。"""
    settings = get_settings()
    key = build_cache_key("rag", "answer", collection, stable_hash({"q": query}))
    _set_json(key, payload, ttl_seconds=settings.redis_answer_ttl_seconds)


def get_cached_retrieval(*, query: str, top_k: int, collection: str) -> dict[str, Any] | None:
    """从缓存中获取向量检索出的原始知识片段。"""
    settings = get_settings()
    key = build_cache_key(
        "rag",
        "retrieval",
        collection,
        stable_hash({"q": query, "top_k": top_k}),
    )
    return _get_json(key, ttl_seconds=settings.redis_retrieval_ttl_seconds)


def set_cached_retrieval(
    *,
    query: str,
    top_k: int,
    collection: str,
    payload: dict[str, Any],
) -> None:
    """将向量检索出的结果存入缓存。"""
    settings = get_settings()
    key = build_cache_key(
        "rag",
        "retrieval",
        collection,
        stable_hash({"q": query, "top_k": top_k}),
    )
    _set_json(key, payload, ttl_seconds=settings.redis_retrieval_ttl_seconds)


def get_cached_embedding(*, text: str, model: str) -> list[float] | None:
    """从缓存中获取文本的 Embedding 向量。"""
    settings = get_settings()
    key = build_cache_key(
        "rag",
        "embedding",
        model,
        stable_hash({"text": text}),
    )
    payload = _get_json(key, ttl_seconds=settings.redis_embedding_ttl_seconds)
    if not payload:
        return None
    vector = payload.get("vector")
    if not isinstance(vector, list):
        return None
    try:
        # 确保返回的是浮点数列表
        return [float(item) for item in vector]
    except Exception:
        return None


def set_cached_embedding(*, text: str, model: str, vector: list[float]) -> None:
    """将文本生成的 Embedding 向量存入缓存。"""
    settings = get_settings()
    key = build_cache_key(
        "rag",
        "embedding",
        model,
        stable_hash({"text": text}),
    )
    _set_json(key, {"vector": vector}, ttl_seconds=settings.redis_embedding_ttl_seconds)


def _get_json(key: str, ttl_seconds: int) -> dict[str, Any] | None:
    """通用内部函数：从 Redis 读取并反序列化 JSON。"""

    _ = ttl_seconds
    try:
        redis_client = get_redis_client()
        raw = redis_client.get(key)
    except Exception:
        return None
    if not raw:
        return None
    try:
        parsed = json.loads(raw)
    except Exception:
        return None
    if isinstance(parsed, dict):
        return parsed
    return None


def _set_json(key: str, payload: dict[str, Any], ttl_seconds: int) -> None:
    """通用内部函数：将 JSON 对象写入 Redis 并设置 TTL（过期时间）。"""

    try:
        redis_client = get_redis_client()
        # 使用 setex 原子性地设置值和过期时间
        redis_client.setex(key, max(1, int(ttl_seconds)), json.dumps(payload, ensure_ascii=False, default=str))
    except Exception:
        # 缓存操作被设计为非阻塞，如果失败，主流程（如检索或推理）仍会继续
        return
