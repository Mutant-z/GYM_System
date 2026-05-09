"""Member query tools.
会员查询工具。

This module exposes member-related query tools for the agent.
这个模块向 agent 暴露会员相关的查询工具。

Scope:
职责范围：
- Query membership status
  - 查询会员状态
- Query member profile
  - 查询会员资料

Profile update or other write operations will be added later.
资料更新等写操作后面再补。
"""

from __future__ import annotations

from langchain_core.tools import tool

from ..services.member_service import query_member_profile as member_profile_service
from ..services.member_service import query_member_status as member_status_service
from ._shared import build_login_required_result, resolve_request_identity, serialize_result


@tool
def query_member_status(user_id: str) -> str:
    """Query membership status for the current user.
    查询当前用户的会员状态。
    """

    identity = resolve_request_identity(user_id=user_id)
    if not identity["auth_token"]:
        return serialize_result(
            build_login_required_result(
                domain="member",
                tool_name="query_member_status",
                request={"user_id": user_id},
            )
        )
    result = member_status_service(user_id=identity["user_id"], auth_token=identity["auth_token"])
    result["request"] = {"user_id": identity["user_id"]}
    return serialize_result(result)


@tool
def query_member_profile(user_id: str) -> str:
    """Query the member profile.
    查询会员资料。
    """

    identity = resolve_request_identity(user_id=user_id)
    if not identity["auth_token"]:
        return serialize_result(
            build_login_required_result(
                domain="member",
                tool_name="query_member_profile",
                request={"user_id": user_id},
            )
        )
    result = member_profile_service(user_id=identity["user_id"], auth_token=identity["auth_token"])
    result["request"] = {"user_id": identity["user_id"]}
    return serialize_result(result)
