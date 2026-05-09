"""Gym room domain service.
场地 / 房间业务服务。

This service owns gym room read operations for the agent.
这个服务负责 agent 的场地查询操作。

Current scope:
当前范围：
- List rooms
  - 查询场地列表
- Query room detail
  - 查询场地详情
- Support simple availability-related lookup
  - 支持简单的可用性查询

Future scope:
未来范围：
- Booking creation helpers
  - 预约创建辅助
"""

from __future__ import annotations

from typing import Any

from ..integrations.java_backend_client import JavaBackendClientError, request_json
from ._domain_utils import error_result, success_result


def list_rooms(
    *,
    user_id: str | None = None,
    auth_token: str | None = None,
) -> dict[str, Any]:
    """List gym rooms.
    查询场地列表。
    """

    request = {"user_id": user_id}
    try:
        response = request_json("GET", "/gym/rooms", auth_token=auth_token, user_id=user_id)
        return success_result(
            domain="gym_room",
            operation="list_rooms",
            request=request,
            data=response.get("data"),
            source="java_backend",
            code=response.get("code"),
            message=response.get("message", "ok"),
        )
    except JavaBackendClientError as exc:
        return error_result(
            domain="gym_room",
            operation="list_rooms",
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


def get_room_detail(
    *,
    room_id: str,
    user_id: str | None = None,
    auth_token: str | None = None,
) -> dict[str, Any]:
    """Query a single room detail.
    查询单个场地详情。
    """

    request = {"room_id": room_id, "user_id": user_id}
    try:
        response = request_json("GET", f"/gym/rooms/{room_id}", auth_token=auth_token, user_id=user_id)
        return success_result(
            domain="gym_room",
            operation="get_room_detail",
            request=request,
            data=response.get("data"),
            source="java_backend",
            code=response.get("code"),
            message=response.get("message", "ok"),
        )
    except JavaBackendClientError as exc:
        return error_result(
            domain="gym_room",
            operation="get_room_detail",
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
