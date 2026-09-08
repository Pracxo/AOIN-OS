"""Pure Ollama native-chat payload builder/parser; never opens sockets."""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .local_endpoint_policy import ENDPOINT, require_local_endpoint
from .local_model_binding import MODEL_TAG, require_model_binding


def build_chat_payload(
    *, prompt: str, model_digest: str, frozen_digest: str,
    schema: Mapping[str, Any] | None = None,
) -> dict[str, object]:
    require_local_endpoint(ENDPOINT)
    require_model_binding(
        model_tag=MODEL_TAG, model_digest=model_digest, frozen_digest=frozen_digest
    )
    if not prompt or len(prompt.encode()) > 262_144:
        raise ValueError("prompt is empty or exceeds the bounded request size")
    payload: dict[str, object] = {
        "model": MODEL_TAG,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "think": "low",
        "keep_alive": "10m",
        "options": {"num_ctx": 32768},
    }
    if schema is not None:
        payload["format"] = dict(schema)
    return payload


def project_response(
    payload: Mapping[str, Any], *, model_digest: str, frozen_digest: str
) -> dict[str, object]:
    require_model_binding(
        model_tag=str(payload.get("model", "")),
        model_digest=model_digest,
        frozen_digest=frozen_digest,
    )
    message = payload.get("message")
    if not isinstance(message, Mapping):
        raise ValueError("local response message missing")
    calls = message.get("tool_calls")
    if calls:
        raise ValueError("tool calls are prohibited for the local pilot")
    content = message.get("content")
    if not isinstance(content, str) or not content:
        raise ValueError("local response content missing")
    return {
        "content_fingerprint": _fingerprint(content),
        "content_bytes": len(content.encode()),
        "trust": "untrusted_local_model_output",
    }


def _fingerprint(value: str) -> str:
    import hashlib
    return hashlib.sha256(value.encode()).hexdigest()
