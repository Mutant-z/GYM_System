# `app/services/` Directory Map

This directory contains the application service layer. The guiding principle is:
keep orchestration, domain logic, and infrastructure concerns separated.

这个目录保存应用服务层。核心原则是：
把编排、领域逻辑和基础设施职责分开。

## Current modules

### `chat_service.py`
- Orchestrates the tool-calling chat loop
- Binds LangChain tools to the model
- Executes tool calls and returns the final answer
- Do not place SQL, HTTP business logic, or RAG internals here

### `rag_service.py`
- Builds knowledge answers from retrieval results
- Combines retrieved context with the prompt and LLM output
- Keep it knowledge-only; do not place business actions here

### `retrieval_service.py`
- Runs Milvus vector search
- Normalizes and filters retrieval results
- Used only by knowledge/RAG flows

### `ingest_service.py`
- Loads raw documents
- Cleans, splits, and embeds them
- Writes processed chunks into Milvus

### `memory_service.py`
- Stores conversation history
- Stores pending write actions that still need confirmation
- Provides context for multi-turn chat

### `cache_service.py`
- Caches answers, retrieval results, and embeddings
- Supports rate limiting and idempotency helpers

### `task_service.py`
- Tracks ingestion jobs
- Reports progress and retry metadata

### `intent_service.py`
- Lightweight intent helper for experiments or debugging
- Not part of the main `/chat` tool-calling flow

### `booking_service.py`
- Owns booking query and booking write operations
- Validates booking ownership, conflicts, and availability

### `order_service.py`
- Owns order query and order write operations
- Validates order state and ownership

### `cart_service.py`
- Owns cart item read and write operations
- Validates cart ownership, stock, and selection constraints

### `course_service.py`
- Owns course listing, detail lookup, enrollment, and cancellation
- Validates course availability and enrollment rules

### `member_service.py`
- Owns member status and profile operations
- Validates whether a user can book or enroll

### `commodity_service.py`
- Owns commodity listing, stock query, and purchase-related lookups
- Validates stock and purchase constraints

### `gym_room_service.py`
- Owns room and venue availability lookups
- Supports booking-related availability decisions

Each domain service should focus on one business area and expose a small, stable API to the tool layer.

每个领域服务都应只聚焦一个业务域，并向工具层提供一个小而稳定的接口。
