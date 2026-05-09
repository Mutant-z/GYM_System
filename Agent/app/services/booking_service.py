"""Booking domain service.
预约业务服务。

This service owns booking read operations for the agent.
这个服务负责 agent 的预约类查询操作。

Current scope:
当前范围：
- Query the current user's booking list
  - 查询当前用户的预约列表
- Query one booking from the list by booking id or booking number
  - 根据预约 ID 或预约号从列表中定位单条预约

Future scope:
未来范围：
- Create booking
  - 创建预约
- Cancel booking
  - 取消预约
- Validate booking conflicts and availability
  - 校验预约冲突和可用性

Implementation note:
实现说明：
- Prefer the Java backend API first
  - 优先调用 Java 后端 API
- The current code returns a normalized payload so the tool layer can be thin
  - 当前代码返回统一结构，方便工具层保持轻量
"""

from __future__ import annotations

from typing import Any

from ..integrations.java_backend_client import JavaBackendClientError, request_json
from ._domain_utils import error_result, success_result


def _match_booking_identifier(item: dict[str, Any], booking_id: str) -> bool:
    """Match a booking item by its identifier.
    根据标识匹配预约项。
    """

    candidates = [item.get("id"), item.get("bookingNo"), item.get("booking_no"), item.get("bookingId")]
    return any(str(candidate) == str(booking_id) for candidate in candidates if candidate is not None)


def query_my_bookings(
    *,
    status: str | None = None,
    user_id: str | None = None,
    auth_token: str | None = None,
) -> dict[str, Any]:
    """Query the current user's booking list.
    查询当前用户的预约列表。
    """

    request = {"status": status, "user_id": user_id}
    try:
        response = request_json(
            "GET",
            "/gym/bookings/me",
            params={"status": status} if status else None,
            auth_token=auth_token,
            user_id=user_id,
        )
        return success_result(
            domain="booking",
            operation="query_my_bookings",
            request=request,
            data=response.get("data"),
            source="java_backend",
            code=response.get("code"),
            message=response.get("message", "ok"),
        )
    except JavaBackendClientError as exc:
        return error_result(
            domain="booking",
            operation="query_my_bookings",
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


def query_booking_detail(
    *,
    booking_id: str,
    user_id: str | None = None,
    auth_token: str | None = None,
) -> dict[str, Any]:
    """Query one booking from the current user's booking list.
    从当前用户预约列表中查询单条预约。
    """

    request = {"booking_id": booking_id, "user_id": user_id}
    try:
        response = request_json(
            "GET",
            "/gym/bookings/me",
            auth_token=auth_token,
            user_id=user_id,
        )
        items = response.get("data") or []
        matched_item = next((item for item in items if isinstance(item, dict) and _match_booking_identifier(item, booking_id)), None)
        return success_result(
            domain="booking",
            operation="query_booking_detail",
            request=request,
            data=matched_item,
            source="java_backend",
            code=response.get("code"),
            message=response.get("message", "ok"),
        )
    except JavaBackendClientError as exc:
        return error_result(
            domain="booking",
            operation="query_booking_detail",
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


def create_booking(
    *,
    gym_room_id: str,
    start_time: str,
    end_time: str,
    head_count: int,
    remark: str | None = None,
    user_id: str | None = None,
    auth_token: str | None = None,
) -> dict[str, Any]:
    """Create a new gym booking.
    创建新的健身房预约。
    """

    request = {
        "gym_room_id": gym_room_id,
        "start_time": start_time,
        "end_time": end_time,
        "head_count": head_count,
        "remark": remark,
        "user_id": user_id,
    }
    try:
        response = request_json(
            "POST",
            "/gym/bookings",
            json_body={
                "gymRoomId": gym_room_id,
                "startTime": start_time,
                "endTime": end_time,
                "headCount": head_count,
                "remark": remark,
            },
            auth_token=auth_token,
            user_id=user_id,
        )
        return success_result(
            domain="booking",
            operation="create_booking",
            request=request,
            data=response.get("data"),
            source="java_backend",
            code=response.get("code"),
            message=response.get("message", "ok"),
        )
    except JavaBackendClientError as exc:
        return error_result(
            domain="booking",
            operation="create_booking",
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


def cancel_booking(
    *,
    booking_identifier: str,
    user_id: str | None = None,
    auth_token: str | None = None,
) -> dict[str, Any]:
    """Cancel an existing booking.
    取消已有预约。
    """

    request = {"booking_identifier": booking_identifier, "user_id": user_id}
    try:
        list_response = request_json(
            "GET",
            "/gym/bookings/me",
            auth_token=auth_token,
            user_id=user_id,
        )
        items = list_response.get("data") or []
        matched_item = next(
            (item for item in items if isinstance(item, dict) and _match_booking_identifier(item, booking_identifier)),
            None,
        )
        if matched_item is None:
            return error_result(
                domain="booking",
                operation="cancel_booking",
                request=request,
                error="booking not found for the given identifier",
                source="java_backend",
            )

        booking_id = matched_item.get("id") or matched_item.get("bookingId") or matched_item.get("booking_id")
        if booking_id is None:
            return error_result(
                domain="booking",
                operation="cancel_booking",
                request=request,
                error="matched booking is missing id",
                source="java_backend",
            )

        response = request_json(
            "POST",
            f"/gym/bookings/{booking_id}/cancel",
            auth_token=auth_token,
            user_id=user_id,
        )
        result_data = {
            "id": booking_id,
            "bookingNo": matched_item.get("bookingNo") or matched_item.get("booking_no"),
            "status": "CANCELED",
        }
        return success_result(
            domain="booking",
            operation="cancel_booking",
            request=request,
            data=result_data,
            source="java_backend",
            code=response.get("code"),
            message=response.get("message", "ok"),
        )
    except JavaBackendClientError as exc:
        return error_result(
            domain="booking",
            operation="cancel_booking",
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
