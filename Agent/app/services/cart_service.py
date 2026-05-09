"""Cart domain service.
购物车业务服务。

This service owns cart write and read operations for the agent.
这个服务负责 agent 的购物车查询和写入操作。
"""

from __future__ import annotations

from typing import Any

from ..integrations.java_backend_client import JavaBackendClientError, request_json
from ._domain_utils import error_result, success_result


def list_my_cart_items(
    *,
    user_id: str | None = None,
    auth_token: str | None = None,
) -> dict[str, Any]:
    """List the current user's cart items.
    查询当前用户的购物车条目。
    """

    request = {"user_id": user_id}
    try:
        response = request_json("GET", "/cart/items", auth_token=auth_token, user_id=user_id)
        return success_result(
            domain="cart",
            operation="list_my_cart_items",
            request=request,
            data=response.get("data"),
            source="java_backend",
            code=response.get("code"),
            message=response.get("message", "ok"),
        )
    except JavaBackendClientError as exc:
        return error_result(
            domain="cart",
            operation="list_my_cart_items",
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


def add_cart_item(
    *,
    commodity_id: str,
    quantity: int,
    user_id: str | None = None,
    auth_token: str | None = None,
) -> dict[str, Any]:
    """Add a commodity to the current user's cart.
    将商品加入当前用户购物车。
    """

    request = {"commodity_id": commodity_id, "quantity": quantity, "user_id": user_id}
    try:
        response = request_json(
            "POST",
            "/cart/items",
            json_body={
                "commodityId": commodity_id,
                "quantity": quantity,
            },
            auth_token=auth_token,
            user_id=user_id,
        )
        return success_result(
            domain="cart",
            operation="add_cart_item",
            request=request,
            data=response.get("data"),
            source="java_backend",
            code=response.get("code"),
            message=response.get("message", "ok"),
        )
    except JavaBackendClientError as exc:
        return error_result(
            domain="cart",
            operation="add_cart_item",
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


def update_cart_item(
    *,
    cart_item_id: str,
    quantity: int,
    selected: bool,
    user_id: str | None = None,
    auth_token: str | None = None,
) -> dict[str, Any]:
    """Update a cart item.
    更新购物车条目。
    """

    request = {
        "cart_item_id": cart_item_id,
        "quantity": quantity,
        "selected": selected,
        "user_id": user_id,
    }
    try:
        response = request_json(
            "PUT",
            f"/cart/items/{cart_item_id}",
            json_body={
                "quantity": quantity,
                "selected": selected,
            },
            auth_token=auth_token,
            user_id=user_id,
        )
        return success_result(
            domain="cart",
            operation="update_cart_item",
            request=request,
            data=response.get("data"),
            source="java_backend",
            code=response.get("code"),
            message=response.get("message", "ok"),
        )
    except JavaBackendClientError as exc:
        return error_result(
            domain="cart",
            operation="update_cart_item",
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


def delete_cart_item(
    *,
    cart_item_id: str,
    user_id: str | None = None,
    auth_token: str | None = None,
) -> dict[str, Any]:
    """Delete a cart item.
    删除购物车条目。
    """

    request = {"cart_item_id": cart_item_id, "user_id": user_id}
    try:
        response = request_json(
            "DELETE",
            f"/cart/items/{cart_item_id}",
            auth_token=auth_token,
            user_id=user_id,
        )
        return success_result(
            domain="cart",
            operation="delete_cart_item",
            request=request,
            data=response.get("data"),
            source="java_backend",
            code=response.get("code"),
            message=response.get("message", "ok"),
        )
    except JavaBackendClientError as exc:
        return error_result(
            domain="cart",
            operation="delete_cart_item",
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
