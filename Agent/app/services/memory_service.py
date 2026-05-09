"""Conversation memory service.
对话记忆服务。

This module stores short-lived conversation state for the agent.
这个模块负责保存 Agent 的短生命周期会话状态。

Current responsibilities:
当前职责：
- remember pending write actions that still need user confirmation
  - 记住仍需用户确认的待执行写操作
- store conversation messages for multi-turn context
  - 保存多轮对话消息上下文
- provide a simple hook for future chat summaries
  - 为未来的聊天摘要预留入口

This module intentionally stays lightweight and in-memory for now.
这个模块现在刻意保持轻量，并且先使用内存存储。
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Literal

MessageRole = Literal["user", "assistant", "tool", "system"]

_PENDING_ACTIONS: dict[str, dict[str, Any]] = {}
_CONVERSATION_HISTORY: dict[str, dict[str, Any]] = {}

_PENDING_TTL_SECONDS = 15 * 60
_HISTORY_TTL_SECONDS = 24 * 60 * 60
_MAX_HISTORY_MESSAGES = 120
_MAX_RENDERED_MESSAGE_CHARS = 1200


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _conversation_key(*, conversation_id: str | None, user_id: str | None) -> str:
    conversation_part = conversation_id or "default"
    user_part = user_id or "anon"
    return f"{user_part}::{conversation_part}"


def _is_expired(payload: dict[str, Any]) -> bool:
    expires_at = payload.get("expires_at")
    if not isinstance(expires_at, str):
        return True
    try:
        return datetime.fromisoformat(expires_at) <= _now()
    except ValueError:
        return True


def _cleanup_expired() -> None:
    expired_pending_keys = [key for key, payload in _PENDING_ACTIONS.items() if _is_expired(payload)]
    for key in expired_pending_keys:
        _PENDING_ACTIONS.pop(key, None)

    expired_history_keys = [key for key, payload in _CONVERSATION_HISTORY.items() if _is_expired(payload)]
    for key in expired_history_keys:
        _CONVERSATION_HISTORY.pop(key, None)


def _ensure_history_record(*, conversation_id: str | None, user_id: str | None, ttl_seconds: int) -> dict[str, Any]:
    key = _conversation_key(conversation_id=conversation_id, user_id=user_id)
    record = _CONVERSATION_HISTORY.get(key)
    if record and not _is_expired(record):
        return record

    record = {
        "conversation_id": conversation_id,
        "user_id": user_id,
        "messages": [],
        "created_at": _now().isoformat(),
        "updated_at": _now().isoformat(),
        "expires_at": (_now() + timedelta(seconds=ttl_seconds)).isoformat(),
    }
    _CONVERSATION_HISTORY[key] = record
    return record


def _truncate_text(text: str, max_chars: int = _MAX_RENDERED_MESSAGE_CHARS) -> str:
    normalized = (text or "").replace("\r\n", "\n").replace("\r", "\n").strip()
    if len(normalized) <= max_chars:
        return normalized
    return normalized[:max_chars] + "..."


def store_pending_action(
    *,
    conversation_id: str | None,
    user_id: str | None,
    action: dict[str, Any],
    ttl_seconds: int = _PENDING_TTL_SECONDS,
) -> dict[str, Any]:
    """Store a pending action for the current conversation.
    为当前会话保存一个待确认动作。
    """

    _cleanup_expired()
    key = _conversation_key(conversation_id=conversation_id, user_id=user_id)
    payload = {
        "conversation_id": conversation_id,
        "user_id": user_id,
        "action": action,
        "created_at": _now().isoformat(),
        "expires_at": (_now() + timedelta(seconds=ttl_seconds)).isoformat(),
    }
    _PENDING_ACTIONS[key] = payload
    return payload


def get_pending_action(
    *,
    conversation_id: str | None,
    user_id: str | None,
) -> dict[str, Any] | None:
    """Return the pending action for the current conversation, if any.
    返回当前会话的待确认动作，如有。
    """

    _cleanup_expired()
    key = _conversation_key(conversation_id=conversation_id, user_id=user_id)
    payload = _PENDING_ACTIONS.get(key)
    if not payload:
        return None
    return payload


def clear_pending_action(
    *,
    conversation_id: str | None,
    user_id: str | None,
) -> None:
    """Clear the pending action for the current conversation.
    清除当前会话的待确认动作。
    """

    key = _conversation_key(conversation_id=conversation_id, user_id=user_id)
    _PENDING_ACTIONS.pop(key, None)


def append_chat_message(
    *,
    conversation_id: str | None,
    user_id: str | None,
    role: MessageRole,
    content: str,
    tool_name: str | None = None,
    tool_args: dict[str, Any] | None = None,
    tool_call_id: str | None = None,
    metadata: dict[str, Any] | None = None,
    ttl_seconds: int = _HISTORY_TTL_SECONDS,
) -> dict[str, Any]:
    """Append one message to the current conversation history.
    向当前会话历史追加一条消息。
    """

    _cleanup_expired()
    record = _ensure_history_record(conversation_id=conversation_id, user_id=user_id, ttl_seconds=ttl_seconds)
    message = {
        "role": role,
        "content": content,
        "created_at": _now().isoformat(),
    }
    if tool_name:
        message["tool_name"] = tool_name
    if tool_args is not None:
        message["tool_args"] = tool_args
    if tool_call_id:
        message["tool_call_id"] = tool_call_id
    if metadata:
        message["metadata"] = metadata

    messages = record.setdefault("messages", [])
    messages.append(message)
    if len(messages) > _MAX_HISTORY_MESSAGES:
        record["messages"] = messages[-_MAX_HISTORY_MESSAGES:]

    record["updated_at"] = _now().isoformat()
    record["expires_at"] = (_now() + timedelta(seconds=ttl_seconds)).isoformat()
    return message


def get_chat_messages(
    *,
    conversation_id: str | None,
    user_id: str | None,
) -> list[dict[str, Any]]:
    """Return all stored messages for a conversation.
    返回某个会话保存的全部消息。
    """

    _cleanup_expired()
    key = _conversation_key(conversation_id=conversation_id, user_id=user_id)
    record = _CONVERSATION_HISTORY.get(key)
    if not record:
        return []
    messages = record.get("messages") or []
    return [dict(message) for message in messages if isinstance(message, dict)]


def render_chat_history(
    *,
    conversation_id: str | None,
    user_id: str | None,
) -> str:
    """Render stored chat history into a plain-text transcript.
    将保存的会话历史渲染为纯文本记录。
    """

    messages = get_chat_messages(conversation_id=conversation_id, user_id=user_id)
    if not messages:
        return ""

    lines: list[str] = []
    for index, message in enumerate(messages, start=1):
        role = str(message.get("role") or "system")
        content = _truncate_text(str(message.get("content") or ""))
        if not content:
            continue

        if role == "user":
            label = "用户"
        elif role == "assistant":
            label = "Agent"
        elif role == "tool":
            tool_name = str(message.get("tool_name") or "tool")
            label = f"工具[{tool_name}]"
        else:
            label = role

        lines.append(f"{index}. {label}: {content}")

        metadata = message.get("metadata")
        if role == "tool":
            tool_args = message.get("tool_args")
            if tool_args:
                lines.append(f"   参数: {_truncate_text(str(tool_args), 800)}")
        elif metadata:
            lines.append(f"   上下文: {_truncate_text(str(metadata), 800)}")

    return "\n".join(lines).strip()
