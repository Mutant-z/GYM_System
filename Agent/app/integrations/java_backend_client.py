"""Java backend HTTP client.
Java 后端 HTTP 客户端。

This client is intentionally small and focused:
这个客户端刻意保持简单并聚焦：
- send HTTP requests to the Java backend
  - 向 Java 后端发送 HTTP 请求
- normalize the common `ApiResponse` wrapper
  - 统一解析常见的 `ApiResponse` 包装
- surface a consistent Python-friendly result shape
  - 返回一个 Python 友好的统一结果结构

Domain services should use this client instead of talking to `httpx` directly.
领域服务应使用这个客户端，而不要直接和 `httpx` 打交道。
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any
import json

from ..core import get_settings


class JavaBackendClientError(RuntimeError):
    """Raised when the Java backend request fails.
    当 Java 后端请求失败时抛出。
    """

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        url: str | None = None,
        response_text: str | None = None,
        method: str | None = None,
        path: str | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.url = url
        self.response_text = response_text
        self.method = method
        self.path = path


@lru_cache(maxsize=1)
def get_java_backend_base_url() -> str:
    """Return the configured Java backend base URL.
    返回配置好的 Java 后端基础地址。
    """

    return get_settings().java_backend_base_url.rstrip("/")


def _build_headers(auth_token: str | None = None, user_id: str | None = None) -> dict[str, str]:
    """Build a small set of request headers.
    构造一组简洁的请求头。
    """

    headers = {"Content-Type": "application/json"}
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"
    if user_id:
        headers["X-User-Id"] = str(user_id)
    return headers


def _parse_json_response(response: Any) -> dict[str, Any]:
    """Parse a response as JSON.
    将响应解析为 JSON。
    """

    try:
        return response.json()
    except Exception as exc:
        raise JavaBackendClientError(f"Invalid JSON response from Java backend: {exc}") from exc


def _safe_response_text(response: Any) -> str | None:
    """Return a compact text snapshot for diagnostics.
    返回一个简短的响应文本摘要，方便排查问题。
    """

    try:
        text = response.text
    except Exception:
        return None

    if text is None:
        return None

    text = str(text).strip()
    if len(text) > 1000:
        return text[:1000] + "..."
    return text


def _normalize_api_response(payload: dict[str, Any], *, path: str, method: str, request: dict[str, Any]) -> dict[str, Any]:
    """Normalize the Java `ApiResponse` wrapper.
    统一 Java 的 `ApiResponse` 包装。
    """

    if {"code", "message", "data"}.issubset(payload.keys()):
        return {
            "source": "java_backend",
            "path": path,
            "method": method,
            "code": payload.get("code"),
            "message": payload.get("message"),
            "data": payload.get("data"),
            "request": request,
        }

    return {
        "source": "java_backend",
        "path": path,
        "method": method,
        "code": None,
        "message": "ok",
        "data": payload,
        "request": request,
    }


def _extract_api_code(payload: dict[str, Any]) -> int | None:
    """Extract business code from a Java ApiResponse payload.
    从 Java ApiResponse 载荷中提取业务 code。
    """

    code = payload.get("code")
    if isinstance(code, bool):
        return None
    if isinstance(code, int):
        return code
    if isinstance(code, float) and code.is_integer():
        return int(code)
    if isinstance(code, str) and code.strip().isdigit():
        return int(code.strip())
    return None


def request_json(
    method: str,
    path: str,
    *,
    params: dict[str, Any] | None = None,
    json_body: dict[str, Any] | None = None,
    auth_token: str | None = None,
    user_id: str | None = None,
) -> dict[str, Any]:
    """Send a JSON request to the Java backend and return a normalized payload.
    向 Java 后端发送 JSON 请求并返回统一后的结果。
    """

    settings = get_settings()
    base_url = get_java_backend_base_url()
    url = f"{base_url}{path}"
    request_snapshot = {
        "params": params or {},
        "json": json_body or {},
        "user_id": user_id,
    }

    try:
        import httpx
    except ImportError as exc:
        raise JavaBackendClientError("httpx is required for Java backend requests") from exc

    print(
        "[agent] Java backend request start: "
        f"method={method.upper()} path={path} url={url} "
        f"user_id={user_id} params={params or {}} json_keys={list((json_body or {}).keys())}"
    )

    try:
        # Disable environment proxy resolution here so local loopback requests
        # always go straight to the Java backend instead of being captured by
        # macOS system proxy settings.
        with httpx.Client(trust_env=False, timeout=settings.deepseek_timeout_seconds) as client:
            response = client.request(
                method=method.upper(),
                url=url,
                params=params,
                json=json_body,
                headers=_build_headers(auth_token=auth_token, user_id=user_id),
            )
        print(
            "[agent] Java backend response received: "
            f"method={method.upper()} path={path} status={response.status_code} "
            f"body_length={len(getattr(response, 'text', '') or '')}"
        )
        response.raise_for_status()
    except Exception as exc:
        status_code = getattr(getattr(exc, "response", None), "status_code", None)
        response_text = _safe_response_text(getattr(exc, "response", None))
        print(
            "[agent] Java backend request failed: "
            f"method={method.upper()} path={path} status={status_code} url={url} "
            f"response={response_text or '(empty)'} error={exc}"
        )
        raise JavaBackendClientError(
            f"Java backend request failed for {method} {path}: {exc}",
            status_code=status_code,
            url=url,
            response_text=response_text,
            method=method.upper(),
            path=path,
        ) from exc

    payload = _parse_json_response(response)
    if isinstance(payload, dict) and {"code", "message"}.issubset(payload.keys()):
        api_code = _extract_api_code(payload)
        if api_code is not None and api_code != 0:
            response_text = _safe_response_text(response)
            message = str(payload.get("message") or "java backend business error")
            print(
                "[agent] Java backend business failure: "
                f"method={method.upper()} path={path} code={api_code} message={message}"
            )
            raise JavaBackendClientError(
                f"Java backend business failure for {method} {path}: {message}",
                status_code=api_code,
                url=url,
                response_text=response_text,
                method=method.upper(),
                path=path,
            )
    print(
        "[agent] Java backend request success: "
        f"method={method.upper()} path={path} response_keys={list(payload.keys())}"
    )
    return _normalize_api_response(payload, path=path, method=method.upper(), request=request_snapshot)
