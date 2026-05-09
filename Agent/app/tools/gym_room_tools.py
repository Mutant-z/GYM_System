"""Gym room query tools.
场地查询工具。

This module exposes gym-room-related query tools for the agent.
这个模块向 agent 暴露场地相关的查询工具。

Scope:
职责范围：
- Query room list
  - 查询场地列表
- Query room detail and availability
  - 查询场地详情和可用性

Booking creation and cancellation will be added later.
预约创建和取消后面再补。
"""

from __future__ import annotations

from langchain_core.tools import tool

from ..services.gym_room_service import get_room_detail as gym_room_detail_service
from ..services.gym_room_service import list_rooms as list_rooms_service
from ._shared import build_login_required_result, resolve_request_identity, serialize_result


@tool
def query_gym_room(query: str, room_id: str | None = None, date: str | None = None, time_range: str | None = None) -> str:
    """Query gym room availability and details.
    查询场地可用性和详情。
    """

    request = {
        "query": query,
        "room_id": room_id,
        "date": date,
        "time_range": time_range,
    }
    identity = resolve_request_identity()
    if not identity["auth_token"]:
        return serialize_result(
            build_login_required_result(
                domain="gym_room",
                tool_name="query_gym_room",
                request=request,
            )
        )
    if room_id:
        result = gym_room_detail_service(room_id=room_id, auth_token=identity["auth_token"])
    else:
        result = list_rooms_service(auth_token=identity["auth_token"])
    result["request"] = request
    return serialize_result(result)
