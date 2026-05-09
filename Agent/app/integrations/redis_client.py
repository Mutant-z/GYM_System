"""Redis client placeholder.
Redis 客户端占位文件。

This module will provide shared access to cache, memory, locks, and task state.
这个模块后续提供缓存、记忆、锁和任务状态的统一访问。
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from ..core import get_settings


@lru_cache(maxsize=1)
def get_redis_client() -> Any:
    """Build and cache a Redis client from application settings.
    根据应用配置构建并缓存 Redis 客户端。
    """

    settings = get_settings()
    try:
        import redis
    except ImportError as exc:
        raise RuntimeError("redis is required for Redis requests") from exc

    if settings.redis_url:
        return redis.Redis.from_url(
            settings.redis_url,
            password=settings.redis_password or None,
            socket_connect_timeout=3,
            socket_timeout=3,
            decode_responses=True,
        )

    return redis.Redis(
        host=settings.redis_host,
        port=settings.redis_port,
        db=settings.redis_db,
        password=settings.redis_password or None,
        socket_connect_timeout=3,
        socket_timeout=3,
        decode_responses=True,
    )


def ping_redis() -> bool:
    """Check whether Redis is reachable.
    检查 Redis 是否可达。
    """

    return bool(get_redis_client().ping())
