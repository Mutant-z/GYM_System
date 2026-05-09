"""CLI utility to parse local knowledge files into chunk JSONL.
把本地知识文件解析为 chunk JSONL 的命令行脚本。
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Parse RAG source files into chunk JSONL")
    parser.add_argument(
        "--source-dir",
        default="/Users/mutant/Documents/IDEA/GYM_System/Agent/data/gym_rag_data",
        help="Source directory containing raw files",
    )
    parser.add_argument(
        "--output-path",
        default="/Users/mutant/Documents/IDEA/GYM_System/Agent/data/processed/rag_chunks.jsonl",
        help="Output JSONL path",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=800,
        help="Chunk size in characters",
    )
    parser.add_argument(
        "--chunk-overlap",
        type=int,
        default=120,
        help="Overlap size in characters",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parents[1]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    try:
        from app.services.ingest_service import parse_knowledge_base
    except Exception as exc:
        print(f"[parse_rag_data] Failed to import ingest service: {exc}", file=sys.stderr)
        return 1

    summary = parse_knowledge_base(
        source_dir=args.source_dir,
        output_path=args.output_path,
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap,
    )

    print(
        json.dumps(
            {
                "source_dir": summary.source_dir,
                "output_path": summary.output_path,
                "file_count": summary.file_count,
                "document_count": summary.document_count,
                "chunk_count": summary.chunk_count,
                "skipped_document_count": summary.skipped_document_count,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
