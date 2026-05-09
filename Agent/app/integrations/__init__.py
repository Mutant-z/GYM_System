"""Third-party integration clients for external AI infrastructure.
外部 AI 基础设施的第三方集成客户端。
"""

from .deepseek_client import deepseek_is_configured
from .milvus_client import get_milvus_client, ping_milvus
from .mysql_client import MySQLClient, get_mysql_client
from .ollama_client import embed_texts, ping_ollama
from .redis_client import get_redis_client, ping_redis

__all__ = [
    "MySQLClient",
    "deepseek_is_configured",
    "get_milvus_client",
    "get_mysql_client",
    "get_redis_client",
    "embed_texts",
    "ping_milvus",
    "ping_ollama",
    "ping_redis",
]
