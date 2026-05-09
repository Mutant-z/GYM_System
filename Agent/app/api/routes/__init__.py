"""Versioned route modules for health, chat, ingestion, and task management.
用于健康检查、聊天、导入和任务管理的路由模块。
"""

from .chat import router as chat_router
from .health import router as health_router

__all__ = ["chat_router", "health_router"]
