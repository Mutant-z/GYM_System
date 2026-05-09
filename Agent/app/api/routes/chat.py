"""Chat and intent analysis endpoints.
聊天与意图分析接口。
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ...schemas.chat import ChatRequest, ChatResponse
from ...services.chat_service import run_tool_calling_chat

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    """Run the real tool-calling chat flow.
    运行工具调用聊天流程。
    """

    try:
        return run_tool_calling_chat(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
