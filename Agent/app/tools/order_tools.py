"""Order query tools.
订单查询工具。

This module exposes order-related query tools for the agent.
这个模块向 agent 暴露订单相关的查询工具。

Scope:
职责范围：
- Query order list
  - 查询订单列表
- Query order detail
  - 查询订单详情

Write operations are now exposed in this module.
写操作已在此模块接入。
"""

from __future__ import annotations

from typing import Any

from langchain_core.tools import tool

from ..services.order_service import cancel_order as cancel_order_service
from ..services.order_service import create_order as create_order_service
from ..services.order_service import query_order_detail as order_query_detail_service
from ..services.order_service import query_orders
from ._shared import build_login_required_result, resolve_request_identity, serialize_result


@tool
def query_order(query: str, user_id: str | None = None, order_id: str | None = None, status: str | None = None) -> str:
    """Query order records for a user.
    查询某个用户的订单记录。
    """

    request = {
        "query": query,
        "user_id": user_id,
        "order_id": order_id,
        "status": status,
    }
    identity = resolve_request_identity(user_id=user_id)
    if not identity["auth_token"]:
        return serialize_result(
            build_login_required_result(
                domain="order",
                tool_name="query_order",
                request=request,
            )
        )
    if order_id:
        result = order_query_detail_service(
            order_id=order_id,
            user_id=identity["user_id"],
            auth_token=identity["auth_token"],
        )
    else:
        result = query_orders(status=status, user_id=identity["user_id"], auth_token=identity["auth_token"])
    result["request"] = request
    return serialize_result(result)


@tool
def query_order_detail(order_id: str, user_id: str | None = None) -> str:
    """Query a single order detail.
    查询单个订单详情。
    """

    identity = resolve_request_identity(user_id=user_id)
    if not identity["auth_token"]:
        return serialize_result(
            build_login_required_result(
                domain="order",
                tool_name="query_order_detail",
                request={"order_id": order_id, "user_id": user_id},
            )
    )
    result = order_query_detail_service(order_id=order_id, user_id=identity["user_id"], auth_token=identity["auth_token"])
    return serialize_result(result)


@tool
def create_order(
    cart_item_ids: list[int],
    receiver_name: str,
    receiver_phone: str,
    receiver_address: str,
    user_id: str | None = None,
) -> str:
    """Create an order from selected cart items.
    根据已选购物车条目创建订单。
    """

    request = {
        "cart_item_ids": cart_item_ids,
        "receiver_name": receiver_name,
        "receiver_phone": receiver_phone,
        "receiver_address": receiver_address,
        "user_id": user_id,
    }
    identity = resolve_request_identity(user_id=user_id)
    if not identity["auth_token"]:
        return serialize_result(
            build_login_required_result(
                domain="order",
                tool_name="create_order",
                request=request,
            )
    )
    result = create_order_service(
        cart_item_ids=cart_item_ids,
        receiver_name=receiver_name,
        receiver_phone=receiver_phone,
        receiver_address=receiver_address,
        user_id=identity["user_id"],
        auth_token=identity["auth_token"],
    )
    return serialize_result(result)


@tool
def cancel_order(
    order_identifier: str | None = None,
    order_id: str | None = None,
    order_no: str | None = None,
    query: str | None = None,
    user_id: str | None = None,
) -> str:
    """Cancel one unpaid order by id/order number.
    根据订单 ID/订单号取消一个未支付订单。
    """

    request = {
        "order_identifier": order_identifier,
        "order_id": order_id,
        "order_no": order_no,
        "query": query,
        "user_id": user_id,
    }
    identity = resolve_request_identity(user_id=user_id)
    if not identity["auth_token"]:
        return serialize_result(
            build_login_required_result(
                domain="order",
                tool_name="cancel_order",
                request=request,
            )
        )

    final_identifier = (order_identifier or order_id or order_no or "").strip()
    final_query = (query or "").strip()
    if not final_identifier and not final_query:
        return serialize_result(
            {
                "status": "error",
                "domain": "order",
                "operation": "cancel_order",
                "source": "agent",
                "message": "order_identifier/order_id/order_no/query 至少提供一个",
                "request": request,
                "data": None,
            }
        )

    result = cancel_order_service(
        order_identifier=final_identifier or None,
        query=final_query or None,
        user_id=identity["user_id"],
        auth_token=identity["auth_token"],
    )
    return serialize_result(result)


@tool
def purchase_order(
    purchase_items: list[dict[str, Any]],
    receiver_name: str | None = None,
    receiver_phone: str | None = None,
    receiver_address: str | None = None,
    user_id: str | None = None,
) -> str:
    """Create a direct purchase order from matched commodities.
    根据匹配到的商品直接创建购买单。

    Use this tool when the user wants to buy immediately.
    当用户想直接购买时，使用这个工具。
    Do not route direct purchase requests through cart tools first.
    直接购买请求不要先转到购物车工具。
    """

    request = {
        "purchase_items": purchase_items,
        "receiver_name": receiver_name,
        "receiver_phone": receiver_phone,
        "receiver_address": receiver_address,
        "user_id": user_id,
    }
    identity = resolve_request_identity(user_id=user_id)
    if not identity["auth_token"]:
        return serialize_result(
            build_login_required_result(
                domain="order",
                tool_name="purchase_order",
                request=request,
            )
        )

    payload = {
        "status": "success",
        "domain": "order",
        "operation": "purchase_order",
        "source": "agent",
        "message": "purchase plan received",
        "request": request,
        "data": request,
    }
    return serialize_result(payload)
