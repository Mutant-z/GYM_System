"""Knowledge ingestion service for building RAG chunk dataset.
用于构建 RAG chunk 数据集的知识导入服务。
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from ..core import get_settings
from ..processors.cleaner import clean_text
from ..processors.loader import RawDocument, load_documents
from ..processors.splitter import split_text_into_chunks


@dataclass(slots=True)
class IngestSummary:
    """High-level ingestion statistics.
    导入任务的统计摘要。
    """

    source_dir: str
    output_path: str
    file_count: int
    document_count: int
    chunk_count: int
    skipped_document_count: int


def parse_knowledge_base(
    *,
    source_dir: str | Path | None = None,
    output_path: str | Path | None = None,
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
) -> IngestSummary:
    """Parse source files and write normalized chunks to JSONL.
    解析源文件并将标准化 chunk 写入 JSONL。
    """

    settings = get_settings()
    resolved_source_dir = Path(source_dir or settings.raw_data_dir).expanduser().resolve()
    resolved_output_path = Path(
        output_path or Path(settings.processed_data_dir) / "rag_chunks.jsonl"
    ).expanduser().resolve()
    resolved_output_path.parent.mkdir(parents=True, exist_ok=True)

    docs = load_documents(resolved_source_dir)
    source_files = {doc.source_path for doc in docs}

    effective_chunk_size = int(chunk_size or settings.rag_chunk_size)
    effective_chunk_overlap = int(chunk_overlap or settings.rag_chunk_overlap)

    chunk_count = 0
    skipped_document_count = 0

    with resolved_output_path.open("w", encoding="utf-8") as output:
        for doc in docs:
            written = _write_document_chunks(
                output=output,
                doc=doc,
                chunk_size=effective_chunk_size,
                chunk_overlap=effective_chunk_overlap,
            )
            if written == 0:
                skipped_document_count += 1
            chunk_count += written

    return IngestSummary(
        source_dir=str(resolved_source_dir),
        output_path=str(resolved_output_path),
        file_count=len(source_files),
        document_count=len(docs),
        chunk_count=chunk_count,
        skipped_document_count=skipped_document_count,
    )


def _write_document_chunks(
    *,
    output: Any,
    doc: RawDocument,
    chunk_size: int,
    chunk_overlap: int,
) -> int:
    cleaned_text = clean_text(doc.text)
    if not cleaned_text:
        return 0

    base_metadata = {
        "source_file": doc.source_file,
        "source_path": doc.source_path,
        "doc_type": doc.doc_type,
        **{k: v for k, v in doc.metadata.items() if v is not None and str(v).strip() != ""},
    }

    chunks = split_text_into_chunks(
        doc_id=doc.doc_id,
        text=cleaned_text,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        base_metadata=base_metadata,
    )

    for chunk in chunks:
        record = {
            "chunk_id": chunk.chunk_id,
            "doc_id": chunk.doc_id,
            "chunk_index": chunk.chunk_index,
            "text": chunk.text,
            "text_length": len(chunk.text),
            "metadata": chunk.metadata,
        }
        output.write(json.dumps(record, ensure_ascii=False) + "\n")
    return len(chunks)
