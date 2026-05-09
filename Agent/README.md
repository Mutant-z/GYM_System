# Python AI Service

This directory is the standalone Python AI service for the gym system.
这个目录是健身系统独立的 Python AI 服务目录。

## Recommended layout

- `app/`: application source code
  - `app/`：应用源码目录
- `app/api/routes/`: HTTP route definitions
  - `app/api/routes/`：HTTP 路由定义
- `app/services/`: RAG, ingestion, caching, and memory services
  - `app/services/`：RAG、导入、缓存和记忆服务
- `app/integrations/`: external clients for DeepSeek, Ollama, Milvus, and Redis
  - `app/integrations/`：DeepSeek、Ollama、Milvus 和 Redis 的外部客户端封装
- `app/processors/`: document loading, cleaning, and chunking
  - `app/processors/`：文档读取、清洗和切分
- `app/schemas/`: request and response models
  - `app/schemas/`：请求与响应数据模型
- `app/tools/`: optional business tools for later agent expansion
  - `app/tools/`：后续 Agent 扩展用的业务工具
- `app/utils/`: shared helper functions
  - `app/utils/`：共享工具函数
- `data/raw/`: original documents
  - `data/raw/`：原始文档
- `data/processed/`: cleaned and chunked intermediate data
  - `data/processed/`：清洗和切分后的中间数据
- `tests/`: unit and integration tests
  - `tests/`：单元测试和集成测试

## Development rule

Keep this service focused on AI capabilities only. The Java backend should remain the system of record for authentication and business workflows.
保持这个服务只负责 AI 能力。Java 后端继续作为认证和业务流程的主系统。

## One-click startup

Run the launcher from the `Agent/` directory:

```bash
python start_agent.py
```

从 `Agent/` 目录运行启动器：

```bash
python start_agent.py
```

## LangSmith tracing

To enable LangSmith tracing, copy `Agent/.env.example` to `Agent/.env` and set:

- `LANGSMITH_TRACING=true`
- `LANGSMITH_API_KEY=...`
- `LANGSMITH_PROJECT=gym-agent`
- `LANGSMITH_ENDPOINT=` if you use a self-hosted LangSmith instance

复制 `Agent/.env.example` 到 `Agent/.env` 后，填写以下字段即可开启 LangSmith tracing：

- `LANGSMITH_TRACING=true`
- `LANGSMITH_API_KEY=...`
- `LANGSMITH_PROJECT=gym-agent`
- 如果是自建 LangSmith，再填写 `LANGSMITH_ENDPOINT`
