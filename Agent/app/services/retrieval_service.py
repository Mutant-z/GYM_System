"""Hybrid retrieval service for knowledge RAG.
知识问答的混合检索服务（向量 + 关键词兜底）。
"""

from __future__ import annotations

from functools import lru_cache
import json
from pathlib import Path
import re
from typing import Any

from ..core import get_settings
from ..integrations.milvus_client import get_milvus_client
from ..integrations.ollama_client import embed_texts
from .cache_service import (
    get_cached_embedding,
    get_cached_retrieval,
    set_cached_embedding,
    set_cached_retrieval,
)

_QUESTION_TAILS = [
    "有多少种",
    "多少种",
    "有几种",
    "几种",
    "有哪些",
    "有哪几种",
    "怎么用",
    "怎么使用",
    "如何使用",
    "怎么",
    "如何",
    "是什么",
]

_STOP_TERMS = {
    "怎么",
    "如何",
    "多少",
    "几种",
    "什么",
    "是啥",
    "哪些",
    "怎么用",
    "怎么使用",
    "如何使用",
    "请问",
}

_GENERIC_TERMS = {
    "有什么",
    "什么种",
    "多少种",
    "有几种",
    "哪几种",
    "有哪些",
    "如何做",
    "怎么做",
}

_BIGRAM_WHITELIST = {
    "会员",
    "会籍",
    "课程",
    "预约",
    "跑步",
    "卧推",
    "健身",
    "门禁",
    "器械",
    "训练",
    "教练",
    "减脂",
    "增肌",
    "有氧",
}

_TERM_ALIAS_MAP: dict[str, tuple[str, ...]] = {
    "健身卡": ("会员卡", "会籍", "会籍类型", "会员类型"),
    "会员卡": ("会籍", "健身卡", "会籍类型", "会员类型"),
    "会籍": ("会员卡", "健身卡", "会籍类型"),
    "平板卧推架": ("平板卧推", "卧推架", "卧推"),
    "跑步机": ("跑步机系统", "有氧器械"),
}

_ENTITY_ALIAS_GROUPS: list[set[str]] = [
    {"健身卡", "会员卡", "会籍", "会籍类型", "会员类型"},
    {"平板卧推架", "平板卧推", "卧推架", "卧推"},
    {"跑步机", "跑步机系统"},
]


def retrieve_knowledge(
    *,
    query: str,
    top_k: int | None = None,
    min_score: float | None = None,
) -> dict[str, Any]:
    """Retrieve top knowledge chunks for one query.
    为单个查询召回 top 知识片段。
    """

    text = str(query or "").strip()
    if not text:
        raise ValueError("query must not be empty")

    settings = get_settings()
    collection = settings.milvus_collection
    effective_top_k = max(1, int(top_k or settings.rag_top_k))
    effective_min_score = float(min_score if min_score is not None else settings.rag_min_score)
    model_name = settings.ollama_embed_model
    candidate_k = max(effective_top_k * 6, 30)

    cached_payload = get_cached_retrieval(query=text, top_k=effective_top_k, collection=collection)
    if cached_payload:
        cached_hits_raw = cached_payload.get("hits")
        cached_strategy = str(cached_payload.get("strategy") or "cache")
        cached_hits = [item for item in cached_hits_raw if isinstance(item, dict)] if isinstance(cached_hits_raw, list) else []
        if cached_hits and cached_strategy in {"hybrid_keyword_fallback", "cache_refresh_keyword_fallback"}:
            return {
                "status": "success",
                "query": text,
                "top_k": effective_top_k,
                "min_score": effective_min_score,
                "collection": collection,
                "hits": cached_hits,
                "strategy": cached_strategy,
                "from_cache": True,
            }
        if cached_hits and not _needs_lexical_fallback(query=text, hits=cached_hits[:effective_top_k]):
            return {
                "status": "success",
                "query": text,
                "top_k": effective_top_k,
                "min_score": effective_min_score,
                "collection": collection,
                "hits": cached_hits,
                "strategy": cached_strategy,
                "from_cache": True,
            }
        if cached_hits:
            lexical_hits = _keyword_fallback_search(query=text, limit=max(effective_top_k * 4, 20))
            if lexical_hits:
                refreshed_hits = _merge_hits(primary=lexical_hits, secondary=cached_hits, limit=effective_top_k)
                refreshed_strategy = "cache_refresh_keyword_fallback"
                set_cached_retrieval(
                    query=text,
                    top_k=effective_top_k,
                    collection=collection,
                    payload={"hits": refreshed_hits, "strategy": refreshed_strategy},
                )
                return {
                    "status": "success",
                    "query": text,
                    "top_k": effective_top_k,
                    "min_score": effective_min_score,
                    "collection": collection,
                    "hits": refreshed_hits,
                    "strategy": refreshed_strategy,
                    "from_cache": False,
                }

    vector = get_cached_embedding(text=text, model=model_name)
    if vector is None:
        vectors = embed_texts([text], model=model_name)
        if not vectors:
            raise RuntimeError("Failed to generate query embedding")
        vector = vectors[0]
        set_cached_embedding(text=text, model=model_name, vector=vector)

    client = get_milvus_client()
    raw = client.search(
        collection_name=collection,
        data=[vector],
        limit=candidate_k,
        output_fields=[
            "chunk_id",
            "text",
            "doc_id",
            "chunk_index",
            "source_file",
            "source_path",
            "doc_type",
        ],
        anns_field="vector",
        search_params={"metric_type": "COSINE"},
    )

    raw_hits: list[dict[str, Any]] = []
    if isinstance(raw, list) and raw:
        first = raw[0]
        if isinstance(first, list):
            raw_hits = [item for item in first if isinstance(item, dict)]

    normalized_hits = _normalize_hits(raw_hits, source="vector")
    filtered_hits = [hit for hit in normalized_hits if float(hit.get("score", 0.0)) >= effective_min_score]
    if not filtered_hits and normalized_hits:
        filtered_hits = normalized_hits[: max(effective_top_k, 8)]

    strategy = "vector"
    final_hits = filtered_hits[:effective_top_k]

    if _needs_lexical_fallback(query=text, hits=final_hits):
        lexical_hits = _keyword_fallback_search(query=text, limit=max(effective_top_k * 4, 20))
        if lexical_hits:
            final_hits = _merge_hits(primary=lexical_hits, secondary=filtered_hits, limit=effective_top_k)
            strategy = "hybrid_keyword_fallback"

    if not final_hits and normalized_hits:
        final_hits = normalized_hits[:effective_top_k]
        strategy = "vector_unfiltered_fallback"

    result = {
        "status": "success",
        "query": text,
        "top_k": effective_top_k,
        "min_score": effective_min_score,
        "collection": collection,
        "hits": final_hits,
        "strategy": strategy,
        "from_cache": False,
    }
    set_cached_retrieval(
        query=text,
        top_k=effective_top_k,
        collection=collection,
        payload={"hits": final_hits, "strategy": strategy},
    )
    return result


def _normalize_hits(raw_hits: list[dict[str, Any]], *, source: str) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    for index, hit in enumerate(raw_hits, start=1):
        entity = hit.get("entity")
        entity_dict = entity if isinstance(entity, dict) else {}
        text = str(entity_dict.get("text") or "").strip()
        if not text:
            continue
        score_raw = hit.get("distance")
        try:
            score = float(score_raw)
        except Exception:
            score = 0.0
        chunk_id = str(entity_dict.get("chunk_id") or hit.get("id") or f"chunk-{index}")
        hits.append(
            {
                "rank": index,
                "score": score,
                "chunk_id": chunk_id,
                "doc_id": str(entity_dict.get("doc_id") or ""),
                "chunk_index": int(entity_dict.get("chunk_index") or 0),
                "source_file": str(entity_dict.get("source_file") or ""),
                "source_path": str(entity_dict.get("source_path") or ""),
                "doc_type": str(entity_dict.get("doc_type") or ""),
                "text": text,
                "retrieval_source": source,
            }
        )
    return hits


def _needs_lexical_fallback(*, query: str, hits: list[dict[str, Any]]) -> bool:
    if not hits:
        return True
    terms = _extract_query_terms(query)
    signal_terms = _signal_terms(terms)
    if signal_terms:
        terms = signal_terms
    if not terms:
        return False

    top_hits = hits[: min(6, len(hits))]
    max_overlap = 0
    for hit in top_hits:
        max_overlap = max(max_overlap, _term_overlap_count(terms, str(hit.get("text") or "")))

    best_score = max(float(hit.get("score") or 0.0) for hit in top_hits)
    longest_term = max(terms, key=len)
    longest_in_top = any(longest_term in str(hit.get("text") or "") for hit in top_hits)

    if max_overlap == 0:
        return True
    if not longest_in_top and len(longest_term) >= 4:
        return True
    if best_score < 0.7 and max_overlap < 2:
        return True
    return False


def _extract_query_terms(text: str) -> list[str]:
    normalized = str(text or "").strip()
    if not normalized:
        return []
    compact = re.sub(r"\s+", "", normalized).lower()
    terms: set[str] = set()
    if len(compact) >= 2:
        terms.add(compact)

    # Strip common question tails to expose core entities.
    simplified = compact
    for tail in _QUESTION_TAILS:
        simplified = simplified.replace(tail, "")
    simplified = re.sub(r"[?？:：,，。!！；;、]", "", simplified)
    if len(simplified) >= 2:
        terms.add(simplified)
        terms.update(_expand_term_aliases(simplified))
    terms.update(_expand_term_aliases(compact))

    for token in re.findall(r"[\u4e00-\u9fff]{2,}|[a-zA-Z0-9]+", compact):
        if len(token) >= 2:
            if token in _STOP_TERMS:
                continue
            terms.add(token)
            terms.update(_expand_term_aliases(token))
            # Chinese phrase n-grams improve lexical recall on long questions.
            if re.fullmatch(r"[\u4e00-\u9fff]{4,}", token):
                max_ngram = min(6, len(token))
                for n in range(3, max_ngram + 1):
                    for start in range(0, len(token) - n + 1):
                        terms.add(token[start : start + n])
    terms = {term for term in terms if term not in _STOP_TERMS and len(term) >= 2}
    return sorted(terms, key=len, reverse=True)


def _term_overlap_count(terms: list[str], text: str) -> int:
    haystack = str(text or "").lower()
    if not haystack:
        return 0
    return sum(1 for term in terms if term and term in haystack)


def _merge_hits(
    *,
    primary: list[dict[str, Any]],
    secondary: list[dict[str, Any]],
    limit: int,
) -> list[dict[str, Any]]:
    merged: list[dict[str, Any]] = []
    seen: set[str] = set()
    for source_hits in (primary, secondary):
        for hit in source_hits:
            chunk_id = str(hit.get("chunk_id") or "")
            if not chunk_id or chunk_id in seen:
                continue
            seen.add(chunk_id)
            merged.append(dict(hit))
            if len(merged) >= limit:
                break
        if len(merged) >= limit:
            break

    for index, hit in enumerate(merged, start=1):
        hit["rank"] = index
    return merged


def _keyword_fallback_search(*, query: str, limit: int) -> list[dict[str, Any]]:
    terms = _extract_query_terms(query)
    if not terms:
        return []

    compact_query = re.sub(r"\s+", "", query).lower()
    alias_groups = _query_alias_groups(compact_query)
    asks_type_count = _asks_for_type_count(compact_query)
    scored: list[tuple[float, dict[str, Any]]] = []
    for record in _load_local_chunks():
        text = str(record.get("text") or "")
        if not text:
            continue
        text_lower = text.lower()
        text_compact = re.sub(r"\s+", "", text_lower)

        score = 0.0
        if compact_query and compact_query in text_compact:
            score += 8.0
        if asks_type_count and any(token in text_compact for token in ("会籍", "会员卡", "会员类型", "会籍类型", "月卡", "季卡", "年卡", "次卡")):
            score += 3.0
        for group in alias_groups:
            if any(alias in text_compact for alias in group):
                score += 4.0
        for term in terms:
            if term in text_compact:
                weight = _term_weight(term)
                if weight <= 0:
                    continue
                freq = text_compact.count(term)
                score += min(6.0, weight * (0.9 + 0.25 * min(freq, 6)))

        if score <= 0:
            continue
        hit = {
            "rank": 0,
            "score": score,
            "chunk_id": str(record.get("chunk_id") or ""),
            "doc_id": str(record.get("doc_id") or ""),
            "chunk_index": int(record.get("chunk_index") or 0),
            "source_file": str(record.get("source_file") or ""),
            "source_path": str(record.get("source_path") or ""),
            "doc_type": str(record.get("doc_type") or ""),
            "text": text,
            "retrieval_source": "keyword_fallback",
        }
        scored.append((score, hit))

    scored.sort(key=lambda item: item[0], reverse=True)
    hits = [hit for _, hit in scored[: max(1, limit)]]
    for index, hit in enumerate(hits, start=1):
        hit["rank"] = index
    return hits


@lru_cache(maxsize=1)
def _load_local_chunks() -> list[dict[str, Any]]:
    path = _resolve_chunk_jsonl_path()
    if not path.exists():
        return []

    chunks: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for raw in handle:
            line = raw.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
            except Exception:
                continue
            if not isinstance(payload, dict):
                continue
            text = str(payload.get("text") or "").strip()
            if not text:
                continue
            metadata = payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {}
            chunks.append(
                {
                    "chunk_id": str(payload.get("chunk_id") or ""),
                    "doc_id": str(payload.get("doc_id") or ""),
                    "chunk_index": int(payload.get("chunk_index") or 0),
                    "text": text,
                    "source_file": str(metadata.get("source_file") or ""),
                    "source_path": str(metadata.get("source_path") or ""),
                    "doc_type": str(metadata.get("doc_type") or ""),
                }
            )
    return chunks


def _resolve_chunk_jsonl_path() -> Path:
    settings = get_settings()
    base = Path(settings.processed_data_dir)
    if not base.is_absolute():
        base = Path(__file__).resolve().parents[2] / base
    return base / "rag_chunks.jsonl"


def _expand_term_aliases(term: str) -> set[str]:
    normalized = str(term or "").strip().lower()
    if len(normalized) < 2:
        return set()

    aliases: set[str] = set()
    for key, linked in _TERM_ALIAS_MAP.items():
        candidates = {key, *linked}
        if any(item in normalized for item in candidates) or normalized in candidates:
            aliases.update(candidates)
    aliases.discard(normalized)
    return aliases


def _term_weight(term: str) -> float:
    token = str(term or "").strip().lower()
    if len(token) < 2:
        return 0.0
    if token in _GENERIC_TERMS:
        return 0.0
    if len(token) == 2 and token not in _BIGRAM_WHITELIST:
        return 0.15
    if len(token) == 3:
        return 0.75
    if len(token) >= 4:
        return 1.25 + min(1.5, 0.12 * len(token))
    return 1.0


def _signal_terms(terms: list[str]) -> list[str]:
    result = [term for term in terms if _term_weight(term) >= 1.2]
    if result:
        return result
    return [term for term in terms if len(term) >= 4]


def _query_alias_groups(compact_query: str) -> list[set[str]]:
    groups: list[set[str]] = []
    for group in _ENTITY_ALIAS_GROUPS:
        if any(alias in compact_query for alias in group):
            groups.append(group)
    return groups


def _asks_for_type_count(compact_query: str) -> bool:
    return any(marker in compact_query for marker in ("多少种", "几种", "种类", "类型", "有哪些", "有哪几种"))
