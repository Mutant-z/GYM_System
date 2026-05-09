"""Shared helpers for LangChain tools.
LangChain 工具共享辅助方法。

This module contains small helpers that keep the tool layer uniform.
这个模块提供一些小的辅助方法，让 tool 层的输出格式保持一致。
"""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
import json
from typing import Any


_REQUEST_CONTEXT: ContextVar[dict[str, Any] | None] = ContextVar("agent_request_context", default=None)


@contextmanager
def request_context_scope(
    *,
    user_id: str | None = None,
    auth_token: str | None = None,
    conversation_id: str | None = None,
    metadata: dict[str, Any] | None = None,
):
    """Expose the current chat request to tool functions.
    将当前聊天请求暴露给 tool 函数使用。

    Tools are static LangChain callables, so this request-local context lets
    tool functions read the authenticated user information without adding the
    same boilerplate to every tool signature.
    """

    token = _REQUEST_CONTEXT.set(
        {
            "user_id": user_id,
            "auth_token": auth_token,
            "conversation_id": conversation_id,
            "metadata": metadata or {},
        }
    )
    try:
        yield
    finally:
        _REQUEST_CONTEXT.reset(token)


def get_request_context() -> dict[str, Any]:
    """Return the current request context for tool execution.
    返回当前 tool 执行所对应的请求上下文。
    """

    return _REQUEST_CONTEXT.get() or {}


def resolve_request_identity(user_id: str | None = None, auth_token: str | None = None) -> dict[str, str | None]:
    """Resolve credentials from explicit arguments and the request context.
    从显式参数和请求上下文中解析登录信息。
    """

    context = get_request_context()
    resolved_user_id = user_id or context.get("user_id")
    resolved_auth_token = auth_token or context.get("auth_token")
    return {
        "user_id": resolved_user_id,
        "auth_token": resolved_auth_token,
    }


def build_login_required_result(*, domain: str, tool_name: str, request: dict[str, Any]) -> dict[str, Any]:
    """Build a consistent login-required error payload.
    构造统一的“需要登录”错误返回。
    """

    return {
        "status": "error",
        "domain": domain,
        "operation": tool_name,
        "source": "agent",
        "message": "login required before querying system data",
        "request": request,
        "data": None,
    }


def build_stub_result(
    *,
    domain: str,
    tool_name: str,
    request: dict[str, Any],
    note: str,
) -> str:
    """Build a structured placeholder response for a tool call.
    为一次工具调用生成结构化占位响应。

    The current tool layer is intentionally lightweight:
    当前 tool 层故意保持轻量：
    - it documents the query intent
      - 记录查询意图
    - it keeps a stable request shape for the future service layer
      - 为未来 service 层保留稳定的请求结构
    - it returns a JSON string that the LLM can read easily
      - 返回 LLM 容易理解的 JSON 字符串
    """

    payload = {
        "domain": domain,
        "tool": tool_name,
        "status": "stub",
        "request": request,
        "note": note,
    }
    return json.dumps(payload, ensure_ascii=False)


def serialize_result(payload: dict[str, Any]) -> str:
    """Serialize a service result to a JSON string.
    将 service 结果序列化为 JSON 字符串。
    """

    return json.dumps(payload, ensure_ascii=False, default=str)
