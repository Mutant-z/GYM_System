"""End-to-end ingestion script: parse files -> embed -> upsert to Milvus.
端到端导入脚本：解析文件 -> 向量化 -> 写入 Milvus。
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
from typing import Any, Iterable


DEFAULT_SOURCE_DIR = "/Users/mutant/Documents/IDEA/GYM_System/Agent/data/gym_rag_data"
DEFAULT_CHUNK_OUTPUT = "/Users/mutant/Documents/IDEA/GYM_System/Agent/data/processed/rag_chunks.jsonl"

# Set to True if you want to run this script without passing CLI args.
# 设置为 True 后，可直接运行脚本并使用下面的固定参数。
USE_INLINE_CONFIG = True


# 内联运行配置类，用于在不使用命令行参数的情况下快速配置运行参数
@dataclass(slots=True)
class InlineRunConfig:
    source_dir: str = DEFAULT_SOURCE_DIR        # 原始解析文件的存放目录
    chunk_output: str = DEFAULT_CHUNK_OUTPUT    # 解析后的中间 chunk JSONL 文件路径
    collection: str = "gym_agent_docs"          # Milvus 集合名称
    embed_model: str = "bge-large:latest"       # 使用的嵌入模型名称（通过 Ollama）
    batch_size: int = 64                        # 向量化和写入的批处理大小
    # bge-large 模型在较小的 chunk 窗口下通常表现更好
    chunk_size: int = 480                       # 每个文本分片的最大字符数
    chunk_overlap: int = 80                     # 分片之间的重叠字符数
    drop_existing: bool = False                 # 写入前是否删除已有的同名集合
    skip_parse: bool = False                    # 是否跳过解析阶段，直接使用现有的 JSONL 文件
    dry_run: bool = False                       # 仅执行解析和向量化，不实际写入 Milvus
    verify_query: list[str] | None = None       # 导入完成后用于验证检索效果的测试问题
    verify_top_k: int = 3                       # 验证检索时的 Top-k 数量


# 如果 USE_INLINE_CONFIG 为 True，可以在这里直接修改配置
INLINE_CONFIG = InlineRunConfig(
    # 示例：
    # drop_existing=True,
    # skip_parse=True,
)


@dataclass(slots=True)
class ScriptSummary:
    source_dir: str
    chunk_path: str
    collection: str
    record_count: int
    upserted_count: int
    skipped_count: int
    vector_dim: int
    started_at: str
    ended_at: str


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Parse, embed and ingest RAG chunks into Milvus")
    parser.add_argument("--source-dir", default=DEFAULT_SOURCE_DIR, help="Raw source files directory")
    parser.add_argument("--chunk-output", default=DEFAULT_CHUNK_OUTPUT, help="Intermediate chunk JSONL path")
    parser.add_argument("--collection", default="", help="Milvus collection name (default from .env)")
    parser.add_argument("--embed-model", default="", help="Override OLLAMA_EMBED_MODEL")
    parser.add_argument("--batch-size", type=int, default=128, help="Embedding/upsert batch size")
    parser.add_argument("--chunk-size", type=int, default=0, help="Override RAG_CHUNK_SIZE")
    parser.add_argument("--chunk-overlap", type=int, default=0, help="Override RAG_CHUNK_OVERLAP")
    parser.add_argument("--drop-existing", action="store_true", help="Drop collection before ingestion")
    parser.add_argument("--skip-parse", action="store_true", help="Skip parsing and reuse existing chunk JSONL")
    parser.add_argument("--dry-run", action="store_true", help="Run parse and embedding but skip Milvus writes")
    parser.add_argument(
        "--verify-query",
        action="append",
        default=[],
        help="Optional query text for search verification (can repeat)",
    )
    parser.add_argument("--verify-top-k", type=int, default=3, help="Top-k for verification search")
    return parser


def main() -> int:
    """脚本主入口：执行解析、向量化和导入的全流程。"""
    parser = build_parser()
    args = parser.parse_args()
    # 如果开启了内联配置且没有通过命令行传参，则应用内联配置
    if USE_INLINE_CONFIG and len(sys.argv) == 1:
        args = _apply_inline_config(args, INLINE_CONFIG)

    # 动态将项目根目录添加到引导路径，确保应用模块可导入
    project_root = Path(__file__).resolve().parents[1]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    from app.core import get_settings
    from app.integrations.milvus_client import get_milvus_client
    from app.integrations.ollama_client import embed_texts
    from app.services.ingest_service import parse_knowledge_base

    settings = get_settings()
    collection = args.collection.strip() or settings.milvus_collection
    if not collection:
        raise ValueError("Milvus collection name is empty")
    if args.batch_size <= 0:
        raise ValueError("--batch-size must be > 0")

    started_at = datetime.now(timezone.utc).isoformat()

    chunk_size = int(args.chunk_size or settings.rag_chunk_size)
    chunk_overlap = int(args.chunk_overlap or settings.rag_chunk_overlap)
    if chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be smaller than chunk_size")

    chunk_path = Path(args.chunk_output).expanduser().resolve()
    source_dir = Path(args.source_dir).expanduser().resolve()

    # 第一阶段：解析原始文件为文本分片 (Chunks)
    if not args.skip_parse:
        parse_summary = parse_knowledge_base(
            source_dir=source_dir,
            output_path=chunk_path,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
        print(
            "[ingest] parsed: "
            f"files={parse_summary.file_count} docs={parse_summary.document_count} "
            f"chunks={parse_summary.chunk_count} output={parse_summary.output_path}"
        )
    elif not chunk_path.exists():
        raise FileNotFoundError(f"Chunk file does not exist: {chunk_path}")

    # 读取生成的 JSONL 文件记录
    records = list(load_chunk_records(chunk_path))
    if not records:
        raise RuntimeError(f"No chunk records found in {chunk_path}")

    # 获取嵌入模型名称，并通过第一个 chunk 探测向量维度
    model_name = (args.embed_model or settings.ollama_embed_model or "").strip()
    if not model_name:
        raise ValueError("Embedding model is empty. Set OLLAMA_EMBED_MODEL or inline embed_model")

    print(
        "[ingest] config: "
        f"collection={collection} model={model_name} batch_size={args.batch_size} "
        f"skip_parse={args.skip_parse} drop_existing={args.drop_existing} dry_run={args.dry_run}"
    )

    # 预检：确保嵌入服务正常工作并确认维度（如 bge-large 对应 1024 维）
    probe_vector = embed_texts([records[0]["text"]], model=model_name)
    if not probe_vector:
        raise RuntimeError("Embedding probe returned empty result")
    vector_dim = len(probe_vector[0])
    print(f"[ingest] embedding ready: model={model_name} dim={vector_dim}")

    upserted_count = 0
    skipped_count = 0

    if args.dry_run:
        print("[ingest] dry-run enabled, skipping Milvus writes")
    else:
        # 第二阶段：创建/获取 Milvus 集合并写入数据
        client = get_milvus_client()
        ensure_collection(
            client=client,
            collection_name=collection,
            vector_dim=vector_dim,
            drop_existing=args.drop_existing,
        )
        
        # 分批次进行向量化和导入，防止内存溢出或请求过大
        for batch in batched(records, args.batch_size):
            texts = [record["text"] for record in batch]
            # 调用嵌入模型生成向量
            vectors = embed_texts(texts, model=model_name)
            if len(vectors) != len(batch):
                raise RuntimeError("Embedding result count does not match batch size")

            payload: list[dict[str, Any]] = []
            for record, vector in zip(batch, vectors, strict=True):
                if not record["text"]:
                    skipped_count += 1
                    continue
                # 构建写入 Milvus 的完整载体（Payload）
                payload.append(
                    {
                        "chunk_id": record["chunk_id"],       # 主键 ID
                        "vector": vector,                    # 向量数据
                        "text": record["text"],              # 原始文本
                        "text_length": int(record.get("text_length", len(record["text"]))),
                        "doc_id": record.get("doc_id", ""),
                        "chunk_index": int(record.get("chunk_index", 0)),
                        "source_file": record.get("source_file", ""),
                        "source_path": record.get("source_path", ""),
                        "doc_type": record.get("doc_type", ""),
                        "content_hash": sha256_text(record["text"]),
                        "updated_at": datetime.now(timezone.utc).isoformat(),
                    }
                )

            if not payload:
                continue
            # 执行 Upsert 操作（插入或覆盖）
            client.upsert(collection_name=collection, data=payload)
            upserted_count += len(payload)
            print(f"[ingest] upserted batch: size={len(payload)} total={upserted_count}")

        # 将集合加载到内存中，以便后续检索
        client.load_collection(collection)

        # 第三阶段：检索验证（测试一些常见问题，确认召回效果）
        queries = args.verify_query or [
            "会员卡可以暂停吗",
            "跑步机怎么安全使用",
            "如何处理门禁二维码失效",
        ]
        run_verification_search(
            client=client,
            embed_model=model_name,
            collection=collection,
            queries=queries,
            top_k=args.verify_top_k,
        )

    ended_at = datetime.now(timezone.utc).isoformat()
    # 打印流程统计摘要
    summary = ScriptSummary(
        source_dir=str(source_dir),
        chunk_path=str(chunk_path),
        collection=collection,
        record_count=len(records),
        upserted_count=upserted_count,
        skipped_count=skipped_count,
        vector_dim=vector_dim,
        started_at=started_at,
        ended_at=ended_at,
    )
    print(json.dumps(asdict(summary), ensure_ascii=False, indent=2))
    return 0


def load_chunk_records(path: Path) -> Iterable[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        for line_no, raw in enumerate(handle, start=1):
            line = raw.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError as exc:
                raise RuntimeError(f"Invalid JSON at {path}:{line_no}") from exc
            if not isinstance(payload, dict):
                continue

            text = str(payload.get("text") or "").strip()
            if not text:
                continue

            metadata = payload.get("metadata")
            metadata_dict = metadata if isinstance(metadata, dict) else {}
            yield {
                "chunk_id": str(payload.get("chunk_id") or ""),
                "doc_id": str(payload.get("doc_id") or ""),
                "chunk_index": int(payload.get("chunk_index") or 0),
                "text": text,
                "text_length": int(payload.get("text_length") or len(text)),
                "source_file": str(metadata_dict.get("source_file") or ""),
                "source_path": str(metadata_dict.get("source_path") or ""),
                "doc_type": str(metadata_dict.get("doc_type") or ""),
            }


def ensure_collection(
    *,
    client: Any,
    collection_name: str,
    vector_dim: int,
    drop_existing: bool,
) -> None:
    """确保 Milvus 集合存在并配置正确。"""
    exists = bool(client.has_collection(collection_name))
    
    # 如果要求删除旧集合
    if exists and drop_existing:
        print(f"[ingest] dropping existing collection: {collection_name}")
        client.drop_collection(collection_name=collection_name)
        exists = False

    # 若集合已存在，打印当前信息并退出创建逻辑
    if exists:
        info = client.describe_collection(collection_name=collection_name)
        print(f"[ingest] collection exists: {collection_name}")
        print(f"[ingest] collection info: {json.dumps(info, ensure_ascii=False)}")
        return

    # 创建新的集合
    print(f"[ingest] creating collection: {collection_name}")
    client.create_collection(
        collection_name=collection_name,
        dimension=vector_dim,
        primary_field_name="chunk_id",       # 主键字段名
        id_type="string",                   # 主键类型（文本）
        vector_field_name="vector",          # 向量字段名
        metric_type="COSINE",                # 距离度量标准（余弦相似度）
        auto_id=False,                       # 不自动生成 ID，由应用层提供
        max_length=512,                     # 某些字符串字段的最大长度
        enable_dynamic_field=True,           # 启用动态 Schema，支持存储额外的元数据
    )
    # 将集合加载到内存（Milvus 搜索前必须加载）
    client.load_collection(collection_name=collection_name)
    print(f"[ingest] collection created and loaded: {collection_name}")


def run_verification_search(
    *,
    client: Any,
    embed_model: str | None,
    collection: str,
    queries: list[str],
    top_k: int,
) -> None:
    """运行验证搜索，通过几个预设问题检查数据的召回质量。"""
    from app.integrations.ollama_client import embed_texts

    for query in queries:
        query_text = str(query or "").strip()
        if not query_text:
            continue
        # 将测试问题向量化
        vectors = embed_texts([query_text], model=embed_model)
        if not vectors:
            continue
        # 在 Milvus 中执行向量搜索
        hits = client.search(
            collection_name=collection,
            data=vectors,
            limit=max(1, top_k),
            output_fields=["chunk_id", "source_file", "doc_id", "text"], # 指定返回字段
            anns_field="vector",
            search_params={"metric_type": "COSINE"},
        )
        print(f"[verify] query={query_text}")
        if not hits or not hits[0]:
            print("[verify] no hits")
            continue
        # 打印搜索到的 Top-k 结果片段，用于人工核对
        for index, hit in enumerate(hits[0], start=1):
            entity = hit.get("entity", {})
            text = str(entity.get("text") or "").replace("\n", " ")
            snippet = text[:120] + ("..." if len(text) > 120 else "")
            print(
                f"[verify] {index}. score={hit.get('distance')} "
                f"chunk_id={entity.get('chunk_id')} source={entity.get('source_file')} "
                f"snippet={snippet}"
            )


def sha256_text(text: str) -> str:
    """计算文本的 SHA256 哈希值，用于内容排重或版本记录。"""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def batched(items: list[dict[str, Any]], batch_size: int) -> Iterable[list[dict[str, Any]]]:
    """将列表按 batch_size 进行分批迭代。"""
    for start in range(0, len(items), batch_size):
        yield items[start : start + batch_size]


def _apply_inline_config(args: argparse.Namespace, cfg: InlineRunConfig) -> argparse.Namespace:
    """将内联配置对象的属性覆盖到 argparse 的参数对象中。"""
    args.source_dir = cfg.source_dir
    args.chunk_output = cfg.chunk_output
    args.collection = cfg.collection
    args.embed_model = cfg.embed_model
    args.batch_size = cfg.batch_size
    args.chunk_size = cfg.chunk_size
    args.chunk_overlap = cfg.chunk_overlap
    args.drop_existing = cfg.drop_existing
    args.skip_parse = cfg.skip_parse
    args.dry_run = cfg.dry_run
    args.verify_query = list(cfg.verify_query or [])
    args.verify_top_k = cfg.verify_top_k
    return args


if __name__ == "__main__":
    # 以 main 函数的返回值作为退出码
    raise SystemExit(main())
