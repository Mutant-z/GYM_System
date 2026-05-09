"""Ollama embedding client helpers.
Ollama embedding 客户端工具。
"""

from __future__ import annotations

from functools import lru_cache
import time
from typing import Any

from ..core import get_settings


@lru_cache(maxsize=1)
def get_ollama_base_url() -> str:
    """Return the configured Ollama base URL.
    返回配置好的 Ollama 基础地址。
    """

    return get_settings().ollama_base_url.rstrip("/")


def ping_ollama() -> bool:
    """Check whether Ollama is reachable.
    检查 Ollama 是否可达。
    """

    base_url = get_ollama_base_url()
    try:
        import httpx
    except ImportError as exc:
        raise RuntimeError("httpx is required for Ollama requests") from exc

    response = httpx.get(f"{base_url}/api/tags", timeout=3, trust_env=False)
    response.raise_for_status()
    return True


def embed_texts(texts: list[str], model: str | None = None) -> list[list[float]]:
    """Embed multiple texts via Ollama.
    通过 Ollama 对多段文本生成向量。
    """

    cleaned = [str(text or "").strip() for text in texts]
    cleaned = [text for text in cleaned if text]
    if not cleaned:
        return []

    settings = get_settings()
    embed_model = model or settings.ollama_embed_model
    if not embed_model:
        raise ValueError("OLLAMA_EMBED_MODEL is not configured")

    base_url = get_ollama_base_url()
    timeout = settings.ollama_timeout_seconds

    try:
        import httpx
    except ImportError as exc:
        raise RuntimeError("httpx is required for Ollama requests") from exc

    # `trust_env=False` prevents local requests from being hijacked by HTTP proxy env vars.
    with httpx.Client(timeout=timeout, trust_env=False) as client:
        preflight_warning, resolved_model = _assert_model_available(
            client=client,
            base_url=base_url,
            model=embed_model,
        )
        model_for_request = resolved_model or embed_model

        # Preferred endpoint for batch embedding.
        response = _post_with_retries(
            client=client,
            url=f"{base_url}/api/embed",
            json_payload={"model": model_for_request, "input": cleaned},
        )
        if response.status_code < 400:
            payload = response.json()
            embeddings = payload.get("embeddings")
            if isinstance(embeddings, list) and embeddings:
                return _coerce_embedding_batch(embeddings)

        first_error = _format_http_error("POST /api/embed", response)
        if _is_context_too_long_error(response):
            # Fall back to per-text embedding with automatic length backoff.
            vectors: list[list[float]] = []
            for text in cleaned:
                vectors.append(
                    _embed_single_with_backoff(
                        client=client,
                        base_url=base_url,
                        model=model_for_request,
                        text=text,
                    )
                )
            return vectors

        # Backward compatibility endpoint, supports one prompt at a time.
        vectors: list[list[float]] = []
        for text in cleaned:
            single = _post_with_retries(
                client=client,
                url=f"{base_url}/api/embeddings",
                json_payload={"model": model_for_request, "prompt": text},
            )
            if single.status_code >= 400:
                second_error = _format_http_error("POST /api/embeddings", single)
                warning_text = f" preflight_warning={preflight_warning}." if preflight_warning else ""
                raise RuntimeError(
                    "Ollama embedding request failed. "
                    f"primary_error={first_error}; fallback_error={second_error}. "
                    f"{warning_text}"
                    "If you see 'input length exceeds the context length', "
                    "please reduce ingestion chunk_size (e.g. 400-500) or rely on automatic backoff. "
                    "Please ensure Ollama is running and the embedding model is pulled "
                    f"(example: `ollama pull {embed_model}`). "
                    f"resolved_model={model_for_request}."
                )
            payload = single.json()
            embedding = payload.get("embedding")
            if not isinstance(embedding, list) or not embedding:
                raise RuntimeError("Ollama /api/embeddings returned invalid vector payload")
            vectors.append(_coerce_embedding(embedding))
        return vectors


def _coerce_embedding_batch(raw_vectors: list[Any]) -> list[list[float]]:
    vectors: list[list[float]] = []
    for raw in raw_vectors:
        if not isinstance(raw, list):
            raise RuntimeError("Ollama embedding payload is not a list of vectors")
        vectors.append(_coerce_embedding(raw))
    return vectors


def _coerce_embedding(raw: list[Any]) -> list[float]:
    try:
        vector = [float(value) for value in raw]
    except Exception as exc:
        raise RuntimeError("Failed to convert embedding vector to float list") from exc
    if not vector:
        raise RuntimeError("Received empty embedding vector")
    return vector


def _assert_model_available(
    *,
    client: Any,
    base_url: str,
    model: str,
) -> tuple[str | None, str | None]:
    """Validate model exists in local Ollama tag list.
    校验目标模型是否已在本地 Ollama 中可用。
    """

    try:
        response = _get_with_retries(client=client, url=f"{base_url}/api/tags")
        # If service is temporarily unavailable, do not hard-fail here.
        # Let the real embedding request run and return richer diagnostics.
        if response.status_code >= 500:
            return _format_http_error("GET /api/tags", response), None
        if response.status_code >= 400:
            raise RuntimeError(_format_http_error("GET /api/tags", response))
        payload = response.json()
        models = payload.get("models")
        if not isinstance(models, list):
            return None, None
        names: set[str] = set()
        preferred_name: str | None = None
        for item in models:
            if not isinstance(item, dict):
                continue
            name = str(item.get("name") or "").strip()
            model_name = str(item.get("model") or "").strip()
            if name:
                names.add(name)
                if preferred_name is None and (name == model or name.startswith(model + ":")):
                    preferred_name = name
            if model_name:
                names.add(model_name)
                if preferred_name is None and (model_name == model or model_name.startswith(model + ":")):
                    preferred_name = model_name
        # Accept exact match or repo-prefix match (e.g. bge-m3 vs bge-m3:latest).
        if model in names:
            return None, model
        for name in names:
            if name.startswith(model + ":"):
                return None, preferred_name or name
        raise RuntimeError(
            f"Ollama model '{model}' is not available locally. "
            f"Please run `ollama pull {model}` first."
        )
    except Exception as exc:
        if isinstance(exc, RuntimeError):
            raise
        return f"GET /api/tags request failed: {exc}", None


def _format_http_error(action: str, response: Any) -> str:
    body_preview = ""
    try:
        body = response.text or ""
        body_preview = body.strip().replace("\n", " ")
    except Exception:
        body_preview = ""
    if len(body_preview) > 200:
        body_preview = body_preview[:200] + "..."
    return f"{action} -> {response.status_code} ({body_preview})"


def _is_context_too_long_error(response: Any) -> bool:
    if response is None:
        return False
    try:
        body = (response.text or "").lower()
    except Exception:
        body = ""
    return "input length exceeds the context length" in body


def _embed_single_with_backoff(
    *,
    client: Any,
    base_url: str,
    model: str,
    text: str,
) -> list[float]:
    # Try raw text first, then progressively shorter slices.
    candidate_limits = [None, 1200, 900, 700, 512, 420, 360, 300, 240, 200]
    last_error = ""

    for limit in candidate_limits:
        prompt = _truncate_for_embedding(text, limit)
        if not prompt:
            continue
        response = _post_with_retries(
            client=client,
            url=f"{base_url}/api/embeddings",
            json_payload={"model": model, "prompt": prompt},
        )
        if response.status_code < 400:
            payload = response.json()
            embedding = payload.get("embedding")
            if isinstance(embedding, list) and embedding:
                return _coerce_embedding(embedding)
            last_error = "invalid embedding payload"
            continue

        last_error = _format_http_error("POST /api/embeddings", response)
        if _is_context_too_long_error(response):
            continue
        break

    raise RuntimeError(
        "Failed to embed text after context-length backoff. "
        f"last_error={last_error}. "
        "Please reduce chunk_size in ingestion config."
    )


def _truncate_for_embedding(text: str, max_chars: int | None) -> str:
    normalized = str(text or "").strip()
    if not normalized:
        return ""
    if max_chars is None or len(normalized) <= max_chars:
        return normalized
    return normalized[:max_chars]


def _post_with_retries(*, client: Any, url: str, json_payload: dict[str, Any], max_attempts: int = 8) -> Any:
    response = None
    for attempt in range(1, max_attempts + 1):
        response = client.post(url, json=json_payload)
        # Retry only on temporary service unavailable.
        if response.status_code != 503:
            return response
        if attempt < max_attempts:
            time.sleep(min(6.0, 0.8 * attempt))
    return response


def _get_with_retries(*, client: Any, url: str, max_attempts: int = 8) -> Any:
    response = None
    for attempt in range(1, max_attempts + 1):
        response = client.get(url)
        if response.status_code != 503:
            return response
        if attempt < max_attempts:
            time.sleep(min(6.0, 0.8 * attempt))
    return response
