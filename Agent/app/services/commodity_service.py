"""Commodity domain service.
商品业务服务。

This service owns commodity read operations for the agent.
这个服务负责 agent 的商品查询操作。

Current scope:
当前范围：
- Query commodity list
  - 查询商品列表
- Query commodity detail
  - 查询商品详情
- Query commodity stock
  - 查询商品库存

Future scope:
未来范围：
- Purchase flow helpers
  - 购买流程辅助
"""

from __future__ import annotations

from typing import Any

from ..integrations.java_backend_client import JavaBackendClientError, request_json
from ._domain_utils import error_result, success_result


def list_commodities(
    *,
    user_id: str | None = None,
    auth_token: str | None = None,
) -> dict[str, Any]:
    """List commodities.
    查询商品列表。
    """

    request = {"user_id": user_id}
    try:
        response = request_json("GET", "/commodities", auth_token=auth_token, user_id=user_id)
        return success_result(
            domain="commodity",
            operation="list_commodities",
            request=request,
            data=response.get("data"),
            source="java_backend",
            code=response.get("code"),
            message=response.get("message", "ok"),
        )
    except JavaBackendClientError as exc:
        return error_result(
            domain="commodity",
            operation="list_commodities",
            request=request,
            error=str(exc),
            source="java_backend",
            code=getattr(exc, "status_code", None),
            details={
                "url": getattr(exc, "url", None),
                "response_text": getattr(exc, "response_text", None),
                "method": getattr(exc, "method", None),
                "path": getattr(exc, "path", None),
            },
        )


def get_commodity_detail(
    *,
    commodity_id: str,
    user_id: str | None = None,
    auth_token: str | None = None,
) -> dict[str, Any]:
    """Query commodity detail.
    查询商品详情。
    """

    request = {"commodity_id": commodity_id, "user_id": user_id}
    try:
        response = request_json("GET", f"/commodities/{commodity_id}", auth_token=auth_token, user_id=user_id)
        return success_result(
            domain="commodity",
            operation="get_commodity_detail",
            request=request,
            data=response.get("data"),
            source="java_backend",
            code=response.get("code"),
            message=response.get("message", "ok"),
        )
    except JavaBackendClientError as exc:
        return error_result(
            domain="commodity",
            operation="get_commodity_detail",
            request=request,
            error=str(exc),
            source="java_backend",
            code=getattr(exc, "status_code", None),
            details={
                "url": getattr(exc, "url", None),
                "response_text": getattr(exc, "response_text", None),
                "method": getattr(exc, "method", None),
                "path": getattr(exc, "path", None),
            },
        )


def query_stock(
    *,
    commodity_id: str | None = None,
    user_id: str | None = None,
    auth_token: str | None = None,
) -> dict[str, Any]:
    """Query commodity stock.
    查询商品库存。
    """

    request = {"commodity_id": commodity_id, "user_id": user_id}
    if not commodity_id:
        return error_result(
            domain="commodity",
            operation="query_stock",
            request=request,
            error="commodity_id is required for stock query",
            source="service",
        )

    try:
        response = request_json("GET", f"/commodities/{commodity_id}", auth_token=auth_token, user_id=user_id)
        data = response.get("data") or {}
        stock = None
        purchasable = None
        if isinstance(data, dict):
            stock = data.get("stock")
            purchasable = data.get("purchasable")

        return success_result(
            domain="commodity",
            operation="query_stock",
            request=request,
            data={
                "commodity": data,
                "stock": stock,
                "purchasable": purchasable,
            },
            source="java_backend",
            code=response.get("code"),
            message=response.get("message", "ok"),
        )
    except JavaBackendClientError as exc:
        return error_result(
            domain="commodity",
            operation="query_stock",
            request=request,
            error=str(exc),
            source="java_backend",
            code=getattr(exc, "status_code", None),
            details={
                "url": getattr(exc, "url", None),
                "response_text": getattr(exc, "response_text", None),
                "method": getattr(exc, "method", None),
                "path": getattr(exc, "path", None),
            },
        )
