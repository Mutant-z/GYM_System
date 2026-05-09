"""Health-check endpoint placeholder.
健康检查接口占位文件。

Use this route to verify the Python service can boot and reach core dependencies.
通过这个接口确认 Python 服务可以启动，并且可以访问核心依赖。
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from ...core import get_settings
from ...integrations.deepseek_client import deepseek_is_configured
from ...integrations.milvus_client import ping_milvus
from ...integrations.mysql_client import get_mysql_client
from ...integrations.ollama_client import ping_ollama
from ...integrations.redis_client import ping_redis

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
def health_check() -> dict[str, Any]:
    """Return a minimal service health payload.
    返回最小化的服务健康状态。
    """

    settings = get_settings()
    checks: dict[str, dict[str, Any]] = {}

    try:
        checks["mysql"] = {
            "ok": True,
            "detail": "reachable",
        }
        get_mysql_client().ping()
    except Exception as exc:
        checks["mysql"] = {
            "ok": False,
            "detail": str(exc),
        }

    try:
        checks["redis"] = {
            "ok": True,
            "detail": "reachable",
        }
        ping_redis()
    except Exception as exc:
        checks["redis"] = {
            "ok": False,
            "detail": str(exc),
        }

    try:
        checks["milvus"] = {
            "ok": True,
            "detail": "reachable",
        }
        ping_milvus()
    except Exception as exc:
        checks["milvus"] = {
            "ok": False,
            "detail": str(exc),
        }

    try:
        checks["ollama"] = {
            "ok": True,
            "detail": "reachable",
        }
        ping_ollama()
    except Exception as exc:
        checks["ollama"] = {
            "ok": False,
            "detail": str(exc),
        }

    checks["deepseek"] = {
        "ok": deepseek_is_configured(),
        "detail": "configured" if deepseek_is_configured() else "missing_api_key_or_base_url",
    }

    overall_ok = all(item["ok"] for item in checks.values())
    return {
        "status": "ok" if overall_ok else "degraded",
        "service": settings.app_name,
        "env": settings.app_env,
        "debug": settings.app_debug,
        "checks": checks,
    }
