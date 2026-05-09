"""Cart tools.
购物车工具。

This module exposes cart-related tools for the agent.
这个模块向 agent 暴露购物车相关工具。
"""

from __future__ import annotations

from langchain_core.tools import tool

from ..services.cart_service import add_cart_item as add_cart_item_service
from ..services.cart_service import delete_cart_item as delete_cart_item_service
from ..services.cart_service import list_my_cart_items as list_my_cart_items_service
from ..services.cart_service import update_cart_item as update_cart_item_service
from ._shared import build_login_required_result, resolve_request_identity, serialize_result


@tool
def query_my_cart_items(user_id: str | None = None) -> str:
    """List the current user's cart items.
    查询当前用户的购物车条目。
    """

    identity = resolve_request_identity(user_id=user_id)
    if not identity["auth_token"]:
        return serialize_result(
            build_login_required_result(
                domain="cart",
                tool_name="query_my_cart_items",
                request={"user_id": user_id},
            )
        )
    result = list_my_cart_items_service(user_id=identity["user_id"], auth_token=identity["auth_token"])
    return serialize_result(result)


@tool
def add_cart_item(commodity_id: str, quantity: int, user_id: str | None = None) -> str:
    """Add a commodity to cart.
    将商品加入购物车。
    """

    request = {"commodity_id": commodity_id, "quantity": quantity, "user_id": user_id}
    identity = resolve_request_identity(user_id=user_id)
    if not identity["auth_token"]:
        return serialize_result(
            build_login_required_result(
                domain="cart",
                tool_name="add_cart_item",
                request=request,
            )
        )
    result = add_cart_item_service(
        commodity_id=commodity_id,
        quantity=quantity,
        user_id=identity["user_id"],
        auth_token=identity["auth_token"],
    )
    return serialize_result(result)


@tool
def update_cart_item(cart_item_id: str, quantity: int, selected: bool, user_id: str | None = None) -> str:
    """Update a cart item.
    更新购物车条目。
    """

    request = {
        "cart_item_id": cart_item_id,
        "quantity": quantity,
        "selected": selected,
        "user_id": user_id,
    }
    identity = resolve_request_identity(user_id=user_id)
    if not identity["auth_token"]:
        return serialize_result(
            build_login_required_result(
                domain="cart",
                tool_name="update_cart_item",
                request=request,
            )
        )
    result = update_cart_item_service(
        cart_item_id=cart_item_id,
        quantity=quantity,
        selected=selected,
        user_id=identity["user_id"],
        auth_token=identity["auth_token"],
    )
    return serialize_result(result)


@tool
def delete_cart_item(cart_item_id: str, user_id: str | None = None) -> str:
    """Delete a cart item.
    删除购物车条目。
    """

    request = {"cart_item_id": cart_item_id, "user_id": user_id}
    identity = resolve_request_identity(user_id=user_id)
    if not identity["auth_token"]:
        return serialize_result(
            build_login_required_result(
                domain="cart",
                tool_name="delete_cart_item",
                request=request,
            )
        )
    result = delete_cart_item_service(
        cart_item_id=cart_item_id,
        user_id=identity["user_id"],
        auth_token=identity["auth_token"],
    )
    return serialize_result(result)
