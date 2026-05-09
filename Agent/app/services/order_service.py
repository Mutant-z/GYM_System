"""Order domain service.
订单业务服务。

This service owns order read operations for the agent.
这个服务负责 agent 的订单查询操作。

Current scope:
当前范围：
- Query order list
  - 查询订单列表
- Query order detail
  - 查询订单详情

Future scope:
未来范围：
- Create order
  - 创建订单
- Cancel order
  - 取消订单

Implementation note:
实现说明：
- Prefer the Java backend order API
  - 优先调用 Java 后端订单 API
- Keep this layer focused on business data shaping
  - 保持这一层只负责业务数据整理
"""

from __future__ import annotations

import re
from typing import Any

from ..integrations.java_backend_client import JavaBackendClientError, request_json
from ._domain_utils import error_result, success_result


def _filter_orders(orders: list[dict[str, Any]], status: str | None) -> list[dict[str, Any]]:
    """Filter orders by status when needed.
    在需要时按状态过滤订单。
    """

    if not status:
        return orders
    return [item for item in orders if str(item.get("status", "")).lower() == str(status).lower()]


def _normalize_text(value: Any) -> str:
    text = str(value or "").strip().lower()
    return re.sub(r"\s+", "", text)


def _is_cancellable_order(item: dict[str, Any]) -> bool:
    status = str(item.get("status") or "").upper()
    payment_status = str(item.get("paymentStatus") or item.get("payment_status") or "").upper()
    return status == "CREATED" and payment_status == "UNPAID"


def _extract_query_hints(query: str | None) -> dict[str, str]:
    text = str(query or "")
    hints: dict[str, str] = {}

    order_no_match = re.search(r"\b(od[0-9a-zA-Z]+)\b", text, re.IGNORECASE)
    if order_no_match:
        hints["order_no"] = order_no_match.group(1).strip()

    phone_match = re.search(r"(1\d{10})", text)
    if phone_match:
        hints["receiver_phone"] = phone_match.group(1).strip()

    receiver_match = re.search(r"(?:收货人|收件人|联系人)[:：]?\s*([^\s，,。;；]{1,30})", text)
    if receiver_match:
        hints["receiver_name"] = receiver_match.group(1).strip()

    address_match = re.search(r"(?:收货地址|地址)[:：]?\s*([^\n]{2,120})", text)
    if address_match:
        hints["receiver_address"] = address_match.group(1).strip()

    amount_match = re.search(r"(\d+(?:\.\d{1,2})?)\s*元", text)
    if amount_match:
        hints["amount"] = amount_match.group(1).strip()

    hints["raw_query"] = text
    return hints


def _summarize_orders(items: list[dict[str, Any]], limit: int = 5) -> str:
    lines: list[str] = []
    for item in items[:limit]:
        order_no = item.get("orderNo") or item.get("order_no") or item.get("id")
        receiver_name = item.get("receiverName") or item.get("receiver_name") or "--"
        receiver_phone = item.get("receiverPhone") or item.get("receiver_phone") or "--"
        pay_amount = item.get("payAmount") or item.get("pay_amount") or item.get("totalAmount") or item.get("total_amount")
        created_at = item.get("createdAt") or item.get("created_at") or "--"
        lines.append(f"- {order_no} | 金额:{pay_amount} | 收货人:{receiver_name} | 电话:{receiver_phone} | 创建:{created_at}")
    return "\n".join(lines)


def _match_order_identifier(item: dict[str, Any], order_identifier: str) -> bool:
    """Match an order item by id/order_no/orderNo.
    根据 id/order_no/orderNo 匹配订单项。
    """

    target = str(order_identifier).strip().lower()
    if not target:
        return False

    candidates = [
        item.get("id"),
        item.get("orderNo"),
        item.get("order_no"),
        item.get("orderId"),
        item.get("order_id"),
    ]
    for candidate in candidates:
        if candidate is None:
            continue
        if str(candidate).strip().lower() == target:
            return True
    return False


def _looks_like_order_identifier(value: str | None) -> bool:
    text = str(value or "").strip()
    if not text:
        return False
    return bool(re.fullmatch(r"(?:od[0-9a-zA-Z]+|\d+)", text, flags=re.IGNORECASE))


def _score_order_by_hints(item: dict[str, Any], hints: dict[str, str]) -> int:
    score = 0
    raw_query = _normalize_text(hints.get("raw_query"))
    if not raw_query:
        return score

    order_no = str(item.get("orderNo") or item.get("order_no") or "")
    if order_no and _normalize_text(order_no) in raw_query:
        score += 100

    receiver_phone = str(item.get("receiverPhone") or item.get("receiver_phone") or "")
    if receiver_phone and receiver_phone in raw_query:
        score += 60

    receiver_name = str(item.get("receiverName") or item.get("receiver_name") or "")
    if receiver_name and _normalize_text(receiver_name) and _normalize_text(receiver_name) in raw_query:
        score += 25

    receiver_address = str(item.get("receiverAddress") or item.get("receiver_address") or "")
    normalized_address = _normalize_text(receiver_address)
    if normalized_address and normalized_address[:8] and normalized_address[:8] in raw_query:
        score += 25

    amount = hints.get("amount")
    if amount:
        pay_amount = str(item.get("payAmount") or item.get("pay_amount") or item.get("totalAmount") or item.get("total_amount") or "")
        if pay_amount and amount in pay_amount:
            score += 20

    return score


def _list_orders(
    *,
    user_id: str | None = None,
    auth_token: str | None = None,
) -> tuple[list[dict[str, Any]] | None, str | None]:
    try:
        response = request_json("GET", "/orders", auth_token=auth_token, user_id=user_id)
    except JavaBackendClientError as exc:
        return None, str(exc)

    orders = response.get("data")
    if not isinstance(orders, list):
        return None, "order list response is invalid"

    normalized_orders = [item for item in orders if isinstance(item, dict)]
    return normalized_orders, None


def _extract_order_id(item: dict[str, Any] | None) -> str | None:
    if not isinstance(item, dict):
        return None
    for key in ("id", "orderId", "order_id"):
        value = item.get(key)
        if value is None:
            continue
        text = str(value).strip()
        if text:
            return text
    return None


def _extract_order_no(item: dict[str, Any] | None) -> str | None:
    if not isinstance(item, dict):
        return None
    for key in ("orderNo", "order_no"):
        value = item.get(key)
        if value is None:
            continue
        text = str(value).strip()
        if text:
            return text
    return None


def _resolve_order_id(
    *,
    order_identifier: str | None,
    query: str | None = None,
    user_id: str | None = None,
    auth_token: str | None = None,
) -> tuple[str | None, dict[str, Any] | None, str | None, list[dict[str, Any]]]:
    """Resolve an order identifier to a concrete order id.
    将订单标识解析为具体订单 id。
    """

    orders, list_error = _list_orders(user_id=user_id, auth_token=auth_token)
    if list_error:
        return None, None, list_error, []
    assert orders is not None

    raw_identifier = (order_identifier or "").strip()
    hints = _extract_query_hints(query)
    explicit_identifier = (
        raw_identifier if _looks_like_order_identifier(raw_identifier) else (hints.get("order_no") or "")
    ).strip()
    query_text = (query or "").strip()
    if raw_identifier and not _looks_like_order_identifier(raw_identifier):
        query_text = f"{query_text}\n{raw_identifier}".strip()

    if explicit_identifier:
        matched_item = next((item for item in orders if _match_order_identifier(item, explicit_identifier)), None)
        if matched_item is None:
            return None, None, "order not found for the given identifier", []
        order_id = matched_item.get("id") or matched_item.get("orderId") or matched_item.get("order_id")
        if order_id is None:
            return None, matched_item, "matched order is missing id", []
        return str(order_id), matched_item, None, []

    cancellable_orders = [item for item in orders if _is_cancellable_order(item)]
    if not cancellable_orders:
        return None, None, "no cancellable unpaid orders found", []

    if not query_text:
        if len(cancellable_orders) == 1:
            single = cancellable_orders[0]
            order_id = single.get("id") or single.get("orderId") or single.get("order_id")
            if order_id is None:
                return None, single, "matched order is missing id", []
            return str(order_id), single, None, []
        return None, None, "multiple cancellable orders found, please provide order number", cancellable_orders

    scored = [(item, _score_order_by_hints(item, hints)) for item in cancellable_orders]
    scored.sort(key=lambda pair: pair[1], reverse=True)
    best_item, best_score = scored[0]
    if best_score <= 0:
        return None, None, "no cancellable order matched your description", cancellable_orders

    tied = [item for item, score in scored if score == best_score]
    if len(tied) > 1:
        return None, None, "multiple orders matched your description", tied

    order_id = best_item.get("id") or best_item.get("orderId") or best_item.get("order_id")
    if order_id is None:
        return None, best_item, "matched order is missing id", []
    return str(order_id), best_item, None, []


def query_orders(
    *,
    status: str | None = None,
    user_id: str | None = None,
    auth_token: str | None = None,
) -> dict[str, Any]:
    """Query the current user's order list.
    查询当前用户的订单列表。
    """

    request = {"status": status, "user_id": user_id}
    print(f"[agent] order service query_orders start: request={request}")
    try:
        response = request_json("GET", "/orders", auth_token=auth_token, user_id=user_id)
        orders = response.get("data") or []
        if isinstance(orders, list):
            orders = _filter_orders(orders, status)
        print(
            "[agent] order service query_orders success: "
            f"count={len(orders) if isinstance(orders, list) else 'n/a'} code={response.get('code')}"
        )
        return success_result(
            domain="order",
            operation="query_orders",
            request=request,
            data=orders,
            source="java_backend",
            code=response.get("code"),
            message=response.get("message", "ok"),
        )
    except JavaBackendClientError as exc:
        print(
            "[agent] order service query_orders failed: "
            f"status={getattr(exc, 'status_code', None)} error={exc}"
        )
        return error_result(
            domain="order",
            operation="query_orders",
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


def query_order_detail(
    *,
    order_id: str,
    user_id: str | None = None,
    auth_token: str | None = None,
) -> dict[str, Any]:
    """Query a single order detail by id.
    根据订单 ID 查询单个订单详情。
    """

    request = {"order_id": order_id, "user_id": user_id}
    print(f"[agent] order service query_order_detail start: request={request}")
    try:
        response = request_json("GET", f"/orders/{order_id}", auth_token=auth_token, user_id=user_id)
        print(
            "[agent] order service query_order_detail success: "
            f"code={response.get('code')} has_data={response.get('data') is not None}"
        )
        return success_result(
            domain="order",
            operation="query_order_detail",
            request=request,
            data=response.get("data"),
            source="java_backend",
            code=response.get("code"),
            message=response.get("message", "ok"),
        )
    except JavaBackendClientError as exc:
        print(
            "[agent] order service query_order_detail failed: "
            f"status={getattr(exc, 'status_code', None)} error={exc}"
        )
        return error_result(
            domain="order",
            operation="query_order_detail",
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


def create_order(
    *,
    cart_item_ids: list[int],
    receiver_name: str,
    receiver_phone: str,
    receiver_address: str,
    user_id: str | None = None,
    auth_token: str | None = None,
) -> dict[str, Any]:
    """Create a commodity order from selected cart items.
    根据选中的购物车条目创建商品订单。
    """

    request = {
        "cart_item_ids": cart_item_ids,
        "receiver_name": receiver_name,
        "receiver_phone": receiver_phone,
        "receiver_address": receiver_address,
        "user_id": user_id,
    }
    try:
        response = request_json(
            "POST",
            "/orders",
            json_body={
                "cartItemIds": cart_item_ids,
                "receiverName": receiver_name,
                "receiverPhone": receiver_phone,
                "receiverAddress": receiver_address,
            },
            auth_token=auth_token,
            user_id=user_id,
        )
        created_data = response.get("data")
        if not isinstance(created_data, dict):
            return error_result(
                domain="order",
                operation="create_order",
                request=request,
                error="create order response is invalid: missing order data",
                source="java_backend",
                code=response.get("code"),
                details={
                    "path": "/orders",
                    "raw_data": created_data,
                },
            )

        order_id = _extract_order_id(created_data)
        order_no = _extract_order_no(created_data)
        if not order_id and not order_no:
            return error_result(
                domain="order",
                operation="create_order",
                request=request,
                error="create order response is invalid: missing order id and order number",
                source="java_backend",
                code=response.get("code"),
                details={
                    "path": "/orders",
                    "raw_data": created_data,
                },
            )

        if not order_id and order_no:
            orders, list_error = _list_orders(user_id=user_id, auth_token=auth_token)
            if list_error:
                return error_result(
                    domain="order",
                    operation="create_order",
                    request=request,
                    error=f"order created but verification failed when listing orders: {list_error}",
                    source="java_backend",
                    code=response.get("code"),
                    details={
                        "path": "/orders",
                        "order_no": order_no,
                        "create_response_data": created_data,
                    },
                )
            assert orders is not None
            matched = next(
                (
                    item
                    for item in orders
                    if _extract_order_no(item) == order_no
                ),
                None,
            )
            order_id = _extract_order_id(matched)
            if not order_id:
                return error_result(
                    domain="order",
                    operation="create_order",
                    request=request,
                    error="order created but verification failed: cannot resolve order id",
                    source="java_backend",
                    code=response.get("code"),
                    details={
                        "path": "/orders",
                        "order_no": order_no,
                        "create_response_data": created_data,
                    },
                )

        assert order_id is not None
        verified_response = request_json(
            "GET",
            f"/orders/{order_id}",
            auth_token=auth_token,
            user_id=user_id,
        )
        verified_data = verified_response.get("data")
        if not isinstance(verified_data, dict):
            return error_result(
                domain="order",
                operation="create_order",
                request=request,
                error="order created but verification response is invalid",
                source="java_backend",
                code=response.get("code"),
                details={
                    "path": f"/orders/{order_id}",
                    "create_response_data": created_data,
                    "verify_response_data": verified_data,
                },
            )

        return success_result(
            domain="order",
            operation="create_order",
            request=request,
            data=verified_data,
            source="java_backend",
            code=response.get("code"),
            message=response.get("message", "ok"),
        )
    except JavaBackendClientError as exc:
        return error_result(
            domain="order",
            operation="create_order",
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


def _is_missing_route_error(exc: JavaBackendClientError) -> bool:
    status_code = getattr(exc, "status_code", None)
    response_text = str(getattr(exc, "response_text", "") or "")
    if status_code not in (404, 500):
        return False
    return "No static resource" in response_text or "NoResourceFoundException" in response_text


def cancel_order(
    *,
    order_identifier: str | None = None,
    query: str | None = None,
    user_id: str | None = None,
    auth_token: str | None = None,
) -> dict[str, Any]:
    """Cancel one unpaid order by id/order number.
    根据订单 ID/订单号取消一个未支付订单。
    """

    request = {"order_identifier": order_identifier, "query": query, "user_id": user_id}
    resolved_order_id, matched_order, resolve_error, candidate_orders = _resolve_order_id(
        order_identifier=order_identifier,
        query=query,
        user_id=user_id,
        auth_token=auth_token,
    )
    if resolve_error:
        details: dict[str, Any] = {}
        if candidate_orders:
            details["candidates"] = candidate_orders[:8]
        candidate_text = _summarize_orders(candidate_orders) if candidate_orders else ""
        message = resolve_error
        if candidate_text:
            message = f"{resolve_error}。请指定订单号：\n{candidate_text}"
        return error_result(
            domain="order",
            operation="cancel_order",
            request=request,
            error=message,
            source="java_backend",
            code=409 if candidate_orders else None,
            details=details,
        )

    candidate_calls = [
        ("POST", f"/orders/{resolved_order_id}/cancel"),
        ("PUT", f"/orders/{resolved_order_id}/cancel"),
        ("POST", f"/orders/cancel/{resolved_order_id}"),
    ]
    last_error: JavaBackendClientError | None = None
    for method, path in candidate_calls:
        try:
            response = request_json(
                method,
                path,
                auth_token=auth_token,
                user_id=user_id,
            )
            result_data = {
                "id": resolved_order_id,
                "orderNo": (matched_order or {}).get("orderNo") or (matched_order or {}).get("order_no"),
                "status": "CANCELED",
                "paymentStatus": "CANCELED",
            }
            return success_result(
                domain="order",
                operation="cancel_order",
                request=request,
                data=result_data,
                source="java_backend",
                code=response.get("code"),
                message=response.get("message", "ok"),
            )
        except JavaBackendClientError as exc:
            last_error = exc
            # Retry with compatibility endpoints only when route is missing.
            if _is_missing_route_error(exc):
                continue
            return error_result(
                domain="order",
                operation="cancel_order",
                request=request,
                error=str(exc),
                source="java_backend",
                code=getattr(exc, "status_code", None),
                details={
                    "url": getattr(exc, "url", None),
                    "response_text": getattr(exc, "response_text", None),
                    "method": getattr(exc, "method", None),
                    "path": getattr(exc, "path", None),
                    "tried_calls": [f"{m} {p}" for m, p in candidate_calls],
                },
            )

    assert last_error is not None
    if _is_missing_route_error(last_error):
        return error_result(
            domain="order",
            operation="cancel_order",
            request=request,
            error="后端未找到取消订单接口，请重启 Java 服务并确认已加载最新订单控制器路由。",
            source="java_backend",
            code=404,
            details={
                "url": getattr(last_error, "url", None),
                "response_text": getattr(last_error, "response_text", None),
                "method": getattr(last_error, "method", None),
                "path": getattr(last_error, "path", None),
                "tried_calls": [f"{m} {p}" for m, p in candidate_calls],
            },
        )
    return error_result(
        domain="order",
        operation="cancel_order",
        request=request,
        error=str(last_error),
        source="java_backend",
        code=getattr(last_error, "status_code", None),
        details={
            "url": getattr(last_error, "url", None),
            "response_text": getattr(last_error, "response_text", None),
            "method": getattr(last_error, "method", None),
            "path": getattr(last_error, "path", None),
            "tried_calls": [f"{m} {p}" for m, p in candidate_calls],
        },
    )
