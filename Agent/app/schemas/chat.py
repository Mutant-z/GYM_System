"""Chat request and response schemas for the RAG workflow.
用于 RAG 流程的聊天请求与响应数据模型。
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """User chat request.
    用户聊天请求。
    """

    text: str = Field(..., description="User input text")
    user_id: str | None = Field(default=None, description="Optional user identifier")
    auth_token: str | None = Field(default=None, description="Optional login token")
    conversation_id: str | None = Field(default=None, description="Optional conversation identifier")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Optional extra context")


class ChatToolCall(BaseModel):
    """One tool call during agent execution.
    agent 执行过程中的一次工具调用。
    """

    name: str = Field(..., description="Tool name")
    arguments: dict[str, Any] = Field(default_factory=dict, description="Tool arguments")
    result: str = Field(default="", description="Tool result text")


class ChatResponse(BaseModel):
    """Final response returned to the user.
    返回给用户的最终结果。
    """

    answer: str = Field(..., description="Final assistant answer")
    tool_calls: list[ChatToolCall] = Field(default_factory=list, description="Executed tool calls")
    used_tools: list[str] = Field(default_factory=list, description="Names of tools used")
    workflow_state: str = Field(default="completed", description="Current workflow state")
    requires_confirmation: bool = Field(default=False, description="Whether the next user reply should confirm a pending action")
    confirmation_prompt: str | None = Field(default=None, description="Prompt asking the user to confirm a pending action")
    pending_action: dict[str, Any] | None = Field(default=None, description="Stored pending action awaiting confirmation")
