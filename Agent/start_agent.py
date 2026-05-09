"""One-click launcher for the Python AI service.
Python AI 服务的一键启动程序。

Run this file from the `Agent/` directory or by passing its absolute path.
It will start the FastAPI app through Uvicorn using values from `.env`.
可以在 `Agent/` 目录下直接运行，也可以使用绝对路径运行。
它会读取 `.env` 中的配置，并通过 Uvicorn 启动 FastAPI 服务。
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


# Hardcoded launcher behavior.
# 启动器固定行为配置。
LAUNCH_HOST = "0.0.0.0"
LAUNCH_PORT = 8000
LAUNCH_RELOAD = False


def main() -> int:
    """Launch the service process.
    启动服务进程。
    """

    project_root = Path(__file__).resolve().parent
    os.chdir(project_root)

    try:
        from app.core import get_settings
    except Exception as exc:  # pragma: no cover
        print(f"[agent] Failed to import project settings: {exc}", file=sys.stderr)
        return 1

    settings = get_settings()
    host = LAUNCH_HOST
    port = LAUNCH_PORT
    reload_enabled = LAUNCH_RELOAD and settings.app_env.lower() in {"development", "dev", "local"}

    print("[agent] Starting Python AI service")
    print(f"[agent] Root: {project_root}")
    print(f"[agent] App: {settings.app_name}")
    print(f"[agent] Env: {settings.app_env}")
    print(f"[agent] Host: {host}")
    print(f"[agent] Port: {port}")
    print(f"[agent] Reload: {reload_enabled}")
    print(f"[agent] MySQL: {settings.mysql_sqlalchemy_url}")
    print(f"[agent] Redis: {settings.redis_url}")
    print(f"[agent] Milvus: {settings.milvus_host}:{settings.milvus_port}/{settings.milvus_database}")
    print(f"[agent] Ollama: {settings.ollama_base_url}")
    print(f"[agent] DeepSeek: {settings.deepseek_base_url}")
    print(f"[agent] LangSmith tracing: {settings.langsmith_tracing}")
    print(f"[agent] LangSmith project: {settings.langsmith_project}")
    print(f"[agent] LangSmith endpoint: {settings.langsmith_endpoint or '(default cloud)'}")
    print(f"[agent] LangSmith active: {'yes' if settings.langsmith_tracing and settings.langsmith_api_key else 'no'}")
    print("[agent] Launcher parameters are hardcoded in start_agent.py")
    print(f"[agent] Fixed Host: {host}")
    print(f"[agent] Fixed Port: {port}")
    print(f"[agent] Fixed Reload: {reload_enabled}")

    cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "app.main:app",
        "--host",
        str(host),
        "--port",
        str(port),
    ]
    if reload_enabled:
        cmd.append("--reload")

    try:
        completed = subprocess.run(cmd, check=False)
        return completed.returncode
    except KeyboardInterrupt:
        print("\n[agent] Interrupted by user")
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
