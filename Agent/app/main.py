"""Application entrypoint for the Python AI service.
Python AI 服务的应用入口文件。

This file will later create the FastAPI app, register routes, and wire
service dependencies together.
后续会在这里创建 FastAPI 实例、注册路由，并组装服务依赖。
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from .api.routes import chat_router, health_router
from .core import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown hooks.
    处理启动和关闭钩子。
    """

    settings = get_settings()
    print(
        "[agent] LangSmith status: "
        f"tracing={settings.langsmith_tracing}, "
        f"project={settings.langsmith_project}, "
        f"endpoint={settings.langsmith_endpoint or 'default'}"
    )

    yield

    # LangSmith/LangChain traces may still be in flight when the process exits.
    # 这里等待未完成的 trace 提交，尽量避免关服时丢最后几条记录。
    try:
        from langchain_core.tracers.langchain import wait_for_all_tracers
    except ImportError:
        return

    wait_for_all_tracers()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.
    创建并配置 FastAPI 应用。
    """

    settings = get_settings()
    app = FastAPI(title=settings.app_name, debug=settings.app_debug, lifespan=lifespan)
    app.include_router(health_router)
    app.include_router(chat_router)
    return app


app = create_app()
