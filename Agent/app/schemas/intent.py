"""Intent analysis schemas.
意图分析数据模型。
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class IntentAnalysisRequest(BaseModel):
    """Incoming text to analyze.
    待分析的用户输入。
    """

    text: str = Field(..., description="User input text")
    user_id: str | None = Field(default=None, description="Optional user identifier")
    conversation_id: str | None = Field(default=None, description="Optional conversation identifier")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Optional extra context")


class IntentAnalysisResponse(BaseModel):
    """Structured intent analysis result.
    结构化意图分析结果。
    """

    category: Literal["business", "knowledge", "unknown"] = Field(..., description="Top-level category")
    intent: str = Field(..., description="Normalized intent label")
    tool_name: str = Field(..., description="Suggested tool name")
    tool_args: dict[str, Any] = Field(default_factory=dict, description="Arguments for the suggested tool")
    needs_follow_up: bool = Field(default=False, description="Whether more information is needed")
    follow_up_question: str | None = Field(default=None, description="Clarification question when needed")
    missing_parameters: list[str] = Field(default_factory=list, description="Required parameters that are missing")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="Model confidence score")
    reason: str = Field(default="", description="Short explanation of the decision")
    source: Literal["llm", "fallback"] = Field(default="llm", description="Decision source")
