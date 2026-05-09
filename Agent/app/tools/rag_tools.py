"""Knowledge retrieval tools.
知识检索工具。
"""

from __future__ import annotations

from langchain_core.tools import tool

from ..services.rag_service import answer_knowledge_question
from ._shared import serialize_result


@tool
def rag_search(query: str, top_k: int | None = None) -> str:
    """Search the knowledge base and return a grounded answer.
    检索知识库并返回带依据的回答。
    """

    result = answer_knowledge_question(question=query, top_k=top_k)
    payload = {
        "status": "success",
        "domain": "knowledge",
        "operation": "rag_search",
        "source": "agent",
        "message": "knowledge answer generated",
        "request": {"query": query, "top_k": top_k},
        "data": result,
    }
    return serialize_result(payload)


@tool
def web_search(query: str) -> str:
    """Placeholder web search tool.
    网页检索占位工具。
    """

    payload = {
        "status": "error",
        "domain": "knowledge",
        "operation": "web_search",
        "source": "agent",
        "message": "web_search is not enabled in this deployment",
        "request": {"query": query},
        "data": None,
    }
    return serialize_result(payload)
