"""Application service layer overview.
应用服务层总览。

This package groups the app into clear responsibility buckets:
这个包把应用层按职责拆分为几个清晰的模块：

- `chat_service.py`: LangChain orchestration and tool-calling loop
  - `chat_service.py`：LangChain 编排和工具调用循环
- `rag_service.py`: answer generation for knowledge questions
  - `rag_service.py`：知识类问题的回答编排
- `retrieval_service.py`: Milvus vector search and ranking
  - `retrieval_service.py`：Milvus 向量检索与结果排序
- `ingest_service.py`: document ingestion pipeline for the knowledge base
  - `ingest_service.py`：知识库文档导入流水线
- `memory_service.py`: short-term conversation history and summaries
  - `memory_service.py`：短期对话历史和摘要
- `cache_service.py`: Redis cache for answers, retrieval results, and embeddings
  - `cache_service.py`：答案、检索结果和向量缓存
- `task_service.py`: ingestion job tracking and progress reporting
  - `task_service.py`：导入任务跟踪和进度上报

Business-specific operations should live in dedicated domain services such as
`booking_service.py`, `order_service.py`, or `course_service.py` when they are added.
业务类操作后续应放到独立领域服务中，例如新增的 `booking_service.py`、`order_service.py`、`course_service.py`。
"""
