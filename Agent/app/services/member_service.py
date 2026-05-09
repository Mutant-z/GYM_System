"""Member domain service.
会员业务服务。

This service owns member read operations for the agent.
这个服务负责 agent 的会员查询操作。

Current scope:
当前范围：
- Query member profile
  - 查询会员资料
- Query member status
  - 查询会员状态

Future scope:
未来范围：
- Update member profile
  - 更新会员资料
"""

from __future__ import annotations

from typing import Any

from ..integrations.java_backend_client import JavaBackendClientError, request_json
from ._domain_utils import error_result, success_result


def query_member_profile(
    *,
    user_id: str | None = None,
    auth_token: str | None = None,
) -> dict[str, Any]:
    """Query the current member profile.
    查询当前会员资料。
    """

    request = {"user_id": user_id}
    try:
        response = request_json("GET", "/members/me/profile", auth_token=auth_token, user_id=user_id)
        return success_result(
            domain="member",
            operation="query_member_profile",
            request=request,
            data=response.get("data"),
            source="java_backend",
            code=response.get("code"),
            message=response.get("message", "ok"),
        )
    except JavaBackendClientError as exc:
        return error_result(
            domain="member",
            operation="query_member_profile",
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


def query_member_status(
    *,
    user_id: str | None = None,
    auth_token: str | None = None,
) -> dict[str, Any]:
    """Query the current member status.
    查询当前会员状态。
    """

    request = {"user_id": user_id}
    profile_result = query_member_profile(user_id=user_id, auth_token=auth_token)
    if profile_result.get("status") != "success":
        return {
            **profile_result,
            "operation": "query_member_status",
        }

    profile = profile_result.get("data") or {}
    membership_status = None
    if isinstance(profile, dict):
        membership_status = profile.get("membershipStatus") or profile.get("membership_status")

    return success_result(
        domain="member",
        operation="query_member_status",
        request=request,
        data={
            "membership_status": membership_status,
            "profile": profile,
        },
        source=profile_result.get("source", "java_backend"),
        code=profile_result.get("code"),
        message=profile_result.get("message", "ok"),
    )
