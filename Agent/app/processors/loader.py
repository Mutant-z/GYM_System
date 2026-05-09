"""Document loading utilities for RAG ingestion.
RAG 导入流程的文档读取工具。
"""

from __future__ import annotations

from dataclasses import dataclass, field
import csv
import json
from pathlib import Path
from typing import Any, Iterable


SUPPORTED_SUFFIXES = {".txt", ".md", ".jsonl", ".csv"}


@dataclass(slots=True)
class RawDocument:
    """Normalized source document record before cleaning/splitting.
    清洗和切分前的标准化文档记录。
    """

    doc_id: str
    source_file: str
    source_path: str
    doc_type: str
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)


def discover_source_files(source_dir: str | Path) -> list[Path]:
    """Discover supported files recursively from source directory.
    从源目录递归发现支持的文件。
    """

    base = Path(source_dir).expanduser().resolve()
    if not base.exists():
        raise FileNotFoundError(f"Source directory does not exist: {base}")
    if not base.is_dir():
        raise NotADirectoryError(f"Source path is not a directory: {base}")

    files = [
        path
        for path in base.rglob("*")
        if path.is_file() and path.suffix.lower() in SUPPORTED_SUFFIXES
    ]
    files.sort()
    return files


def load_documents(source_dir: str | Path) -> list[RawDocument]:
    """Load all supported documents from a directory tree.
    从目录树加载全部支持格式的文档。
    """

    source_root = Path(source_dir).expanduser().resolve()
    documents: list[RawDocument] = []
    for file_path in discover_source_files(source_root):
        relative_path = str(file_path.relative_to(source_root))
        suffix = file_path.suffix.lower()
        if suffix in {".txt", ".md"}:
            documents.extend(_load_text_like_file(file_path, relative_path))
        elif suffix == ".jsonl":
            documents.extend(_load_jsonl_file(file_path, relative_path))
        elif suffix == ".csv":
            documents.extend(_load_csv_file(file_path, relative_path))
    return documents


def _load_text_like_file(file_path: Path, relative_path: str) -> list[RawDocument]:
    text = file_path.read_text(encoding="utf-8", errors="ignore")
    stem = _safe_stem(relative_path)
    return [
        RawDocument(
            doc_id=f"{stem}#0",
            source_file=file_path.name,
            source_path=relative_path,
            doc_type=file_path.suffix.lower().lstrip("."),
            text=text,
            metadata={"record_type": "full_text"},
        )
    ]


def _load_jsonl_file(file_path: Path, relative_path: str) -> list[RawDocument]:
    documents: list[RawDocument] = []
    stem = _safe_stem(relative_path)

    with file_path.open("r", encoding="utf-8", errors="ignore") as handle:
        for line_no, raw_line in enumerate(handle, start=1):
            line = raw_line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(payload, dict):
                continue

            text = _build_jsonl_text(payload)
            if not text:
                continue
            record_id = str(payload.get("id") or f"line-{line_no}")
            documents.append(
                RawDocument(
                    doc_id=f"{stem}#{record_id}",
                    source_file=file_path.name,
                    source_path=relative_path,
                    doc_type="jsonl",
                    text=text,
                    metadata={
                        "record_type": "jsonl_record",
                        "line_no": line_no,
                        "record_id": record_id,
                        "intent": payload.get("intent"),
                        "persona": payload.get("persona"),
                        "tone": payload.get("tone"),
                    },
                )
            )
    return documents


def _load_csv_file(file_path: Path, relative_path: str) -> list[RawDocument]:
    documents: list[RawDocument] = []
    stem = _safe_stem(relative_path)

    with file_path.open("r", encoding="utf-8", errors="ignore", newline="") as handle:
        reader = csv.DictReader(handle)
        for row_no, row in enumerate(reader, start=1):
            if not isinstance(row, dict):
                continue
            text = _build_csv_row_text(row)
            if not text:
                continue
            documents.append(
                RawDocument(
                    doc_id=f"{stem}#row-{row_no}",
                    source_file=file_path.name,
                    source_path=relative_path,
                    doc_type="csv",
                    text=text,
                    metadata={
                        "record_type": "csv_row",
                        "row_no": row_no,
                    },
                )
            )
    return documents


def _build_jsonl_text(payload: dict[str, Any]) -> str:
    question = _as_text(payload.get("question"))
    answer = _as_text(payload.get("answer"))
    keywords = _serialize_keywords(payload.get("keywords"))
    intro_parts = [
        _as_text(payload.get("intent")),
        _as_text(payload.get("persona")),
        _as_text(payload.get("tone")),
    ]
    intro = " | ".join(part for part in intro_parts if part)

    segments: list[str] = []
    if intro:
        segments.append(f"分类信息: {intro}")
    if question:
        segments.append(f"问题: {question}")
    if answer:
        segments.append(f"回答: {answer}")
    if keywords:
        segments.append(f"关键词: {keywords}")
    return "\n".join(segments).strip()


def _build_csv_row_text(row: dict[str, Any]) -> str:
    pieces: list[str] = []
    for key, value in row.items():
        key_text = _as_text(key)
        value_text = _as_text(value)
        if not key_text or not value_text:
            continue
        pieces.append(f"{key_text}: {value_text}")
    return "\n".join(pieces).strip()


def _serialize_keywords(value: Any) -> str:
    if isinstance(value, list):
        items = [_as_text(item) for item in value]
        items = [item for item in items if item]
        return "、".join(items)
    if isinstance(value, str):
        return value.strip()
    return ""


def _as_text(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    return text


def _safe_stem(relative_path: str) -> str:
    path = Path(relative_path)
    parts = list(path.parts)
    if not parts:
        return "document"
    parts[-1] = Path(parts[-1]).stem
    return "__".join(parts)
