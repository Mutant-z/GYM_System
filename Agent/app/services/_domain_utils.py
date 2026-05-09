"""Shared helpers for domain services.
领域服务共享辅助方法。

These helpers keep query services consistent and easy to evolve.
这些辅助方法用于保持各查询服务输出一致并便于后续演进。
"""

from __future__ import annotations

from typing import Any


def success_result(
    *,
    domain: str,
    operation: str,
    request: dict[str, Any],
    data: Any,
    source: str,
    code: int | None = None,
    message: str = "ok",
) -> dict[str, Any]:
    """Build a normalized success payload.
    构造统一的成功结果。
    """

    return {
        "status": "success",
        "domain": domain,
        "operation": operation,
        "source": source,
        "code": code,
        "message": message,
        "request": request,
        "data": data,
    }


def error_result(
    *,
    domain: str,
    operation: str,
    request: dict[str, Any],
    error: str,
    source: str = "service",
    code: int | None = None,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a normalized error payload.
    构造统一的错误结果。
    """

    return {
        "status": "error",
        "domain": domain,
        "operation": operation,
        "source": source,
        "message": error,
        "code": code,
        "request": request,
        "data": None,
        "details": details or {},
    }
