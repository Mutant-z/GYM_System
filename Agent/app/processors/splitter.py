"""Text splitter for RAG chunk generation.
用于 RAG 分块生成的文本切分器。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class Chunk:
    """One retrieval chunk with traceable metadata.
    带可追溯元数据的检索片段。
    """

    chunk_id: str
    doc_id: str
    chunk_index: int
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)


def split_text_into_chunks(
    *,
    doc_id: str,
    text: str,
    chunk_size: int,
    chunk_overlap: int,
    base_metadata: dict[str, Any] | None = None,
) -> list[Chunk]:
    """Split text into overlap chunks with simple paragraph-aware boundaries.
    按重叠策略切分文本，优先保持段落边界。
    """

    normalized = (text or "").strip()
    if not normalized:
        return []
    if chunk_size <= 0:
        raise ValueError("chunk_size must be > 0")
    if chunk_overlap < 0:
        raise ValueError("chunk_overlap must be >= 0")
    if chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be smaller than chunk_size")

    metadata = dict(base_metadata or {})
    chunks: list[Chunk] = []

    start = 0
    chunk_index = 0
    total = len(normalized)

    while start < total:
        tentative_end = min(total, start + chunk_size)
        end = _prefer_breakpoint(normalized, start, tentative_end)
        if end <= start:
            end = tentative_end

        chunk_text = normalized[start:end].strip()
        if chunk_text:
            chunk_id = f"{doc_id}#chunk-{chunk_index:05d}"
            chunks.append(
                Chunk(
                    chunk_id=chunk_id,
                    doc_id=doc_id,
                    chunk_index=chunk_index,
                    text=chunk_text,
                    metadata=metadata,
                )
            )
            chunk_index += 1

        if end >= total:
            break
        start = max(0, end - chunk_overlap)

    return chunks


def _prefer_breakpoint(text: str, start: int, tentative_end: int) -> int:
    """Try to break chunks near paragraph/sentence boundaries.
    尽量在段落或句子边界附近切分。
    """

    if tentative_end >= len(text):
        return len(text)

    window_min = max(start + 1, tentative_end - 120)
    candidate = tentative_end
    boundary_chars = {"\n", "。", "！", "？", ".", "!", "?", ";", "；"}

    for index in range(tentative_end, window_min - 1, -1):
        if text[index - 1] in boundary_chars:
            candidate = index
            break
    return candidate
