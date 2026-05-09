"""Milvus vector store client placeholder.
Milvus 向量库客户端占位文件。

This module will handle collection management, inserts, and similarity search.
这个模块后续负责集合管理、向量写入和相似度检索。
"""

from __future__ import annotations

from functools import lru_cache
import socket
from typing import Any

from ..core import get_settings


@lru_cache(maxsize=1)
def get_milvus_client() -> Any:
    """Build and cache a Milvus client from application settings.
    根据应用配置构建并缓存 Milvus 客户端。
    """

    settings = get_settings()
    try:
        from pymilvus import MilvusClient
    except ImportError as exc:
        raise RuntimeError("pymilvus is required for Milvus requests") from exc

    token = None
    if settings.milvus_user:
        token = f"{settings.milvus_user}:{settings.milvus_password or ''}"

    if token:
        return MilvusClient(
            uri=f"http://{settings.milvus_host}:{settings.milvus_port}",
            token=token,
            db_name=settings.milvus_database,
        )

    return MilvusClient(
        uri=f"http://{settings.milvus_host}:{settings.milvus_port}",
        db_name=settings.milvus_database,
    )


def ping_milvus() -> bool:
    """Check whether Milvus is reachable.
    检查 Milvus 是否可达。
    """

    settings = get_settings()
    with socket.create_connection((settings.milvus_host, settings.milvus_port), timeout=3):
        pass
    return True
