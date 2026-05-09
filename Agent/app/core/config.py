"""Centralized configuration definitions for AI service runtime settings.
AI 服务运行参数的集中配置定义。

Expected concerns:
- model endpoints
- vector store connection details
- Redis caching settings
- RAG tunables such as chunk size and top-k
- MySQL business data source settings

关注点包括：
- 模型接口地址
- 向量库连接信息
- Redis 缓存配置
- RAG 参数，例如 chunk 大小和 top-k
- MySQL 业务数据源配置
"""

import os
from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings loaded from `.env`.
    从 `.env` 加载的运行时配置。
    """

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[2] / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_name: str = Field(default="gym-agent", alias="APP_NAME")
    app_env: str = Field(default="development", alias="APP_ENV")
    app_host: str = Field(default="0.0.0.0", alias="APP_HOST")
    app_port: int = Field(default=8000, alias="APP_PORT")
    app_debug: bool = Field(default=True, alias="APP_DEBUG")
    app_log_level: str = Field(default="INFO", alias="APP_LOG_LEVEL")
    app_cors_origins: str = Field(default="*", alias="APP_CORS_ORIGINS")

    langsmith_tracing: bool = Field(default=False, alias="LANGSMITH_TRACING")
    langsmith_api_key: str = Field(default="", alias="LANGSMITH_API_KEY")
    langsmith_project: str = Field(default="gym-agent", alias="LANGSMITH_PROJECT")
    langsmith_endpoint: str = Field(default="", alias="LANGSMITH_ENDPOINT")

    deepseek_api_key: str = Field(default="", alias="DEEPSEEK_API_KEY")
    deepseek_base_url: str = Field(default="https://api.deepseek.com", alias="DEEPSEEK_BASE_URL")
    deepseek_model: str = Field(default="deepseek-chat", alias="DEEPSEEK_MODEL")
    deepseek_timeout_seconds: int = Field(default=60, alias="DEEPSEEK_TIMEOUT_SECONDS")
    deepseek_max_retries: int = Field(default=3, alias="DEEPSEEK_MAX_RETRIES")

    ollama_base_url: str = Field(default="http://localhost:11434", alias="OLLAMA_BASE_URL")
    ollama_embed_model: str = Field(default="bge-m3", alias="OLLAMA_EMBED_MODEL")
    ollama_timeout_seconds: int = Field(default=60, alias="OLLAMA_TIMEOUT_SECONDS")

    milvus_host: str = Field(default="localhost", alias="MILVUS_HOST")
    milvus_port: int = Field(default=19530, alias="MILVUS_PORT")
    milvus_user: str = Field(default="", alias="MILVUS_USER")
    milvus_password: str = Field(default="", alias="MILVUS_PASSWORD")
    milvus_database: str = Field(default="default", alias="MILVUS_DATABASE")
    milvus_collection: str = Field(default="gym_agent_docs", alias="MILVUS_COLLECTION")
    milvus_dimension: int = Field(default=1024, alias="MILVUS_DIMENSION")

    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    redis_host: str = Field(default="localhost", alias="REDIS_HOST")
    redis_port: int = Field(default=6379, alias="REDIS_PORT")
    redis_password: str = Field(default="", alias="REDIS_PASSWORD")
    redis_db: int = Field(default=0, alias="REDIS_DB")
    redis_key_prefix: str = Field(default="agent", alias="REDIS_KEY_PREFIX")
    redis_history_ttl_seconds: int = Field(default=86400, alias="REDIS_HISTORY_TTL_SECONDS")
    redis_answer_ttl_seconds: int = Field(default=3600, alias="REDIS_ANSWER_TTL_SECONDS")
    redis_retrieval_ttl_seconds: int = Field(default=3600, alias="REDIS_RETRIEVAL_TTL_SECONDS")
    redis_embedding_ttl_seconds: int = Field(default=604800, alias="REDIS_EMBEDDING_TTL_SECONDS")

    rag_top_k: int = Field(default=4, alias="RAG_TOP_K")
    rag_chunk_size: int = Field(default=800, alias="RAG_CHUNK_SIZE")
    rag_chunk_overlap: int = Field(default=120, alias="RAG_CHUNK_OVERLAP")
    rag_min_score: float = Field(default=0.75, alias="RAG_MIN_SCORE")
    rag_max_context_chars: int = Field(default=6000, alias="RAG_MAX_CONTEXT_CHARS")
    rag_summary_enabled: bool = Field(default=True, alias="RAG_SUMMARY_ENABLED")

    data_dir: str = Field(default="./data", alias="DATA_DIR")
    raw_data_dir: str = Field(default="./data/raw", alias="RAW_DATA_DIR")
    processed_data_dir: str = Field(default="./data/processed", alias="PROCESSED_DATA_DIR")
    ingest_lock_ttl_seconds: int = Field(default=1800, alias="INGEST_LOCK_TTL_SECONDS")

    java_backend_base_url: str = Field(default="http://localhost:8080/api", alias="JAVA_BACKEND_BASE_URL")
    enable_streaming: bool = Field(default=True, alias="ENABLE_STREAMING")
    enable_tool_calling: bool = Field(default=False, alias="ENABLE_TOOL_CALLING")

    mysql_host: str = Field(default="localhost", alias="MYSQL_HOST")
    mysql_port: int = Field(default=3306, alias="MYSQL_PORT")
    mysql_database: str = Field(default="gym_system", alias="MYSQL_DATABASE")
    mysql_username: str = Field(default="root", alias="MYSQL_USERNAME")
    mysql_password: str = Field(default="", alias="MYSQL_PASSWORD")
    mysql_charset: str = Field(default="utf8mb4", alias="MYSQL_CHARSET")
    mysql_pool_size: int = Field(default=5, alias="MYSQL_POOL_SIZE")
    mysql_max_overflow: int = Field(default=10, alias="MYSQL_MAX_OVERFLOW")
    mysql_pool_timeout_seconds: int = Field(default=30, alias="MYSQL_POOL_TIMEOUT_SECONDS")
    mysql_pool_recycle_seconds: int = Field(default=1800, alias="MYSQL_POOL_RECYCLE_SECONDS")
    mysql_echo: bool = Field(default=False, alias="MYSQL_ECHO")

    @field_validator("app_cors_origins", mode="before")
    @classmethod
    def normalize_cors_origins(cls, value: str | list[str]) -> str | list[str]:
        """Allow a comma-separated string or a list for CORS origins.
        允许使用逗号分隔字符串或列表形式配置 CORS 源。
        """

        if isinstance(value, str) and value.strip() == "":
            return "*"
        return value

    @property
    def mysql_sqlalchemy_url(self) -> str:
        """Build the SQLAlchemy MySQL connection URL.
        构造 SQLAlchemy 使用的 MySQL 连接地址。
        """

        password = self.mysql_password or ""
        return (
            f"mysql+pymysql://{self.mysql_username}:{password}"
            f"@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}"
            f"?charset={self.mysql_charset}"
        )


def _apply_runtime_environment(settings: Settings) -> None:
    """Expose selected settings as real environment variables.
    将部分配置同步到真实环境变量中，方便 LangChain/LangSmith 直接读取。
    """

    env_pairs = {
        "LANGSMITH_TRACING": "true" if settings.langsmith_tracing else "false",
        "LANGSMITH_API_KEY": settings.langsmith_api_key,
        "LANGSMITH_PROJECT": settings.langsmith_project,
        "LANGSMITH_ENDPOINT": settings.langsmith_endpoint,
        # Older LangChain versions may still look for these names.
        "LANGCHAIN_TRACING_V2": "true" if settings.langsmith_tracing else "false",
        "LANGCHAIN_API_KEY": settings.langsmith_api_key,
        "LANGCHAIN_PROJECT": settings.langsmith_project,
        "LANGCHAIN_ENDPOINT": settings.langsmith_endpoint,
    }

    for key, value in env_pairs.items():
        if value:
            os.environ[key] = value


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached Settings instance.
    返回缓存后的 Settings 实例，避免重复读取 `.env`。
    """

    settings = Settings()
    _apply_runtime_environment(settings)
    return settings
