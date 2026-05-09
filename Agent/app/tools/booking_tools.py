"""Booking query tools.
预约查询工具。

This module exposes booking-related query tools for the agent.
这个模块向 agent 暴露预约相关的查询工具。

Scope:
职责范围：
- Query booking records
  - 查询预约记录
- Query booking detail
  - 查询预约详情

This module now also exposes booking write tools.
这个模块现在也暴露预约写操作工具。
"""

from __future__ import annotations

from langchain_core.tools import tool

from ..services.booking_service import cancel_booking as cancel_booking_service
from ..services.booking_service import create_booking as create_booking_service
from ..services.booking_service import query_booking_detail as booking_query_detail_service
from ..services.booking_service import query_my_bookings
from ._shared import build_login_required_result, resolve_request_identity, serialize_result


@tool
def query_booking(
    query: str,
    user_id: str | None = None,
    booking_id: str | None = None,
    booking_no: str | None = None,
    date_range: str | None = None,
) -> str:
    """Query booking records for a user.
    查询某个用户的预约记录。
    """

    request = {
        "query": query,
        "user_id": user_id,
        "booking_id": booking_id,
        "booking_no": booking_no,
        "date_range": date_range,
    }
    identity = resolve_request_identity(user_id=user_id)
    if not identity["auth_token"]:
        return serialize_result(
            build_login_required_result(
                domain="booking",
                tool_name="query_booking",
                request=request,
            )
        )
    if booking_id or booking_no:
        result = booking_query_detail_service(
            booking_id=booking_id or booking_no or "",
            user_id=identity["user_id"],
            auth_token=identity["auth_token"],
        )
    else:
        result = query_my_bookings(user_id=identity["user_id"], auth_token=identity["auth_token"])
    result["request"] = request
    return serialize_result(result)


@tool
def create_booking(
    gym_room_id: str,
    start_time: str,
    end_time: str,
    head_count: int,
    remark: str | None = None,
    user_id: str | None = None,
) -> str:
    """Create a gym booking.
    创建健身房预约。
    """

    request = {
        "gym_room_id": gym_room_id,
        "start_time": start_time,
        "end_time": end_time,
        "head_count": head_count,
        "remark": remark,
        "user_id": user_id,
    }
    identity = resolve_request_identity(user_id=user_id)
    if not identity["auth_token"]:
        return serialize_result(
            build_login_required_result(
                domain="booking",
                tool_name="create_booking",
                request=request,
            )
        )
    result = create_booking_service(
        gym_room_id=gym_room_id,
        start_time=start_time,
        end_time=end_time,
        head_count=head_count,
        remark=remark,
        user_id=identity["user_id"],
        auth_token=identity["auth_token"],
    )
    return serialize_result(result)


@tool
def cancel_booking(
    booking_identifier: str | None = None,
    booking_id: str | None = None,
    booking_no: str | None = None,
    user_id: str | None = None,
) -> str:
    """Cancel a gym booking.
    取消健身房预约。
    """

    request = {
        "booking_identifier": booking_identifier,
        "booking_id": booking_id,
        "booking_no": booking_no,
        "user_id": user_id,
    }
    identity = resolve_request_identity(user_id=user_id)
    if not identity["auth_token"]:
        return serialize_result(
            build_login_required_result(
                domain="booking",
                tool_name="cancel_booking",
                request=request,
            )
        )
    final_identifier = (booking_identifier or booking_id or booking_no or "").strip()
    if not final_identifier:
        return serialize_result(
            {
                "status": "error",
                "domain": "booking",
                "operation": "cancel_booking",
                "source": "agent",
                "message": "booking_identifier or booking_id or booking_no is required",
                "request": request,
                "data": None,
            }
        )
    result = cancel_booking_service(
        booking_identifier=final_identifier,
        user_id=identity["user_id"],
        auth_token=identity["auth_token"],
    )
    return serialize_result(result)
