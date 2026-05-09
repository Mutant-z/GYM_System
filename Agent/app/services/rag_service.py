"""Knowledge-only RAG answer orchestration.
仅用于知识问答的 RAG 编排服务。
"""

from __future__ import annotations

from typing import Any

from ..core import get_settings
from ..integrations.deepseek_client import deepseek_is_configured, get_deepseek_chat_model
from .cache_service import get_cached_answer, set_cached_answer
from .retrieval_service import retrieve_knowledge


def answer_knowledge_question(
    *,
    question: str,
    top_k: int | None = None,
) -> dict[str, Any]:
    """Answer one knowledge question via retrieval + generation.
    通过检索 + 生成回答一个知识问题。
    """

    query = str(question or "").strip()
    if not query:
        raise ValueError("question must not be empty")

    settings = get_settings()
    collection = settings.milvus_collection

    cached = get_cached_answer(query=query, collection=collection)
    if cached:
        cached_answer = str(cached.get("answer") or "")
        if _is_insufficient_answer(cached_answer):
            print(f"[rag] answer cache bypassed (insufficient): question='{query[:60]}'")
        else:
            cached_hits_raw = cached.get("hits")
            cached_hits = [item for item in cached_hits_raw if isinstance(item, dict)] if isinstance(cached_hits_raw, list) else []
            if cached_hits:
                print(f"[rag] answer cache hit: question='{query[:60]}' -> llm polish")
                context_text, citations = _build_context_text(hits=cached_hits, max_chars=settings.rag_max_context_chars)
                polished_answer, polished_mode = _generate_answer(
                    question=query,
                    context_text=context_text,
                    citations=citations,
                )
                final_answer = polished_answer if polished_mode == "llm" and polished_answer.strip() else cached_answer
                final_mode = "llm_polish_from_cache" if polished_mode == "llm" else f"cache_{polished_mode}"

                if not _is_insufficient_answer(final_answer):
                    payload = {
                        "answer": final_answer,
                        "citations": citations,
                        "hits": cached_hits,
                        "generation_mode": final_mode,
                    }
                    set_cached_answer(query=query, collection=collection, payload=payload)

                return {
                    "status": "success",
                    "question": query,
                    "answer": final_answer,
                    "citations": citations,
                    "hits": cached_hits,
                    "generation_mode": final_mode,
                    "from_cache": True,
                    "retrieval_from_cache": True,
                    "retrieval_strategy": "answer_cache_polish",
                }

            print(f"[rag] answer cache hit without hits, fallback to retrieval: question='{query[:60]}'")

    retrieval = retrieve_knowledge(query=query, top_k=top_k)
    print(
        "[rag] answer cache miss: "
        f"question='{query[:60]}' retrieval_cache_hit={bool(retrieval.get('from_cache'))} "
        f"strategy={retrieval.get('strategy')}"
    )
    hits = retrieval.get("hits") or []
    if not isinstance(hits, list):
        hits = []

    if not hits:
        answer = "我在当前知识库中没有检索到足够相关的内容。你可以换个说法，我再试一次。"
        return {
            "status": "success",
            "question": query,
            "answer": answer,
            "citations": [],
            "hits": [],
            "generation_mode": "no_hits",
            "from_cache": False,
            "retrieval_from_cache": bool(retrieval.get("from_cache")),
            "retrieval_strategy": str(retrieval.get("strategy") or "unknown"),
        }

    context_text, citations = _build_context_text(hits=hits, max_chars=settings.rag_max_context_chars)
    answer, generation_mode = _generate_answer(question=query, context_text=context_text, citations=citations)
    if not _is_insufficient_answer(answer):
        payload = {
            "answer": answer,
            "citations": citations,
            "hits": hits,
            "generation_mode": generation_mode,
        }
        set_cached_answer(query=query, collection=collection, payload=payload)

    return {
        "status": "success",
        "question": query,
        "answer": answer,
        "citations": citations,
        "hits": hits,
        "generation_mode": generation_mode,
        "from_cache": False,
        "retrieval_from_cache": bool(retrieval.get("from_cache")),
        "retrieval_strategy": str(retrieval.get("strategy") or "unknown"),
    }


def _generate_answer(*, question: str, context_text: str, citations: list[dict[str, Any]]) -> tuple[str, str]:
    if not deepseek_is_configured():
        return _fallback_answer(question=question, citations=citations), "fallback_no_llm"

    try:
        model = get_deepseek_chat_model()
        prompt = (
            "你是健身系统知识助手。请仅基于给定知识片段回答用户问题。\n"
            "要求：\n"
            "1) 不要编造知识片段之外的事实；\n"
            "2) 回答尽量简洁准确；\n"
            "3) 在回答末尾给出引用编号，例如 [1][2]；\n"
            "4) 如果片段不足以直接回答问题，请先明确“未检索到明确结论”，再补充可确认的相关信息；\n"
            "5) 无论能否直接回答，都尽量给出对用户有帮助的下一步建议。\n\n"
            f"用户问题：{question}\n\n"
            f"知识片段：\n{context_text}\n"
        )
        result = model.invoke(prompt)
        answer = str(getattr(result, "content", "") or "").strip()
        if answer:
            return answer, "llm"
    except Exception:
        pass
    return _fallback_answer(question=question, citations=citations), "fallback_error"


def _build_context_text(*, hits: list[dict[str, Any]], max_chars: int) -> tuple[str, list[dict[str, Any]]]:
    lines: list[str] = []
    selected_citations: list[dict[str, Any]] = []
    total_chars = 0

    for index, hit in enumerate(hits, start=1):
        text = str(hit.get("text") or "").strip()
        if not text:
            continue
        source_file = str(hit.get("source_file") or "")
        chunk_id = str(hit.get("chunk_id") or "")
        score = float(hit.get("score") or 0.0)
        block = f"[{index}] source={source_file} chunk={chunk_id} score={score:.4f}\n{text}\n"

        if total_chars + len(block) > max_chars and lines:
            break
        lines.append(block)
        total_chars += len(block)
        selected_citations.append(
            {
                "index": index,
                "chunk_id": chunk_id,
                "source_file": source_file,
                "score": score,
            }
        )

    return "\n".join(lines).strip(), selected_citations


def _fallback_answer(*, question: str, citations: list[dict[str, Any]]) -> str:
    _ = question
    if not citations:
        return "知识库暂无足够信息。"
    refs = "".join(f"[{item.get('index')}]" for item in citations[:3])
    return f"我已从知识库检索到相关内容，请结合引用片段查看详细信息。{refs}"


def _is_insufficient_answer(answer: str) -> bool:
    text = str(answer or "").strip()
    if not text:
        return True
    compact = text.replace(" ", "").replace("\n", "")
    if compact in {
        "知识库暂无足够信息。",
        "知识库暂无足够信息",
        "我在当前知识库中没有检索到足够相关的内容。你可以换个说法，我再试一次。",
    }:
        return True
    if "知识库暂无足够信息" in compact and len(compact) <= 40:
        return True
    if "没有检索到足够相关" in compact and len(compact) <= 60:
        return True
    return False
