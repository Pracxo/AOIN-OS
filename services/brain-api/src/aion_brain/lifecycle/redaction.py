"""Redaction helpers for lifecycle governance."""

from __future__ import annotations

from typing import Any

_SECRET_KEY_PARTS = {
    "api_key",
    "apikey",
    "authorization",
    "bearer",
    "credential",
    "password",
    "private_key",
    "secret",
    "token",
}
_REMOVED_TEXT_MARKERS = (
    "chain-of-thought",
    "chain_of_thought",
    "hidden reasoning",
    "hidden_reasoning",
    "private reasoning",
    "raw prompt",
    "raw_prompt",
    "system prompt:",
    "developer prompt:",
)


def redact_lifecycle_payload(payload: Any) -> Any:
    """Return a lifecycle-safe payload without storing removed raw values."""

    if isinstance(payload, dict):
        redacted: dict[str, Any] = {}
        for key, value in payload.items():
            lowered = str(key).lower().replace("-", "_")
            if any(part in lowered for part in _SECRET_KEY_PARTS):
                redacted[key] = "[REDACTED]"
            elif lowered in {"raw_prompt", "hidden_reasoning", "chain_of_thought"}:
                redacted[key] = "[REMOVED]"
            else:
                redacted[key] = redact_lifecycle_payload(value)
        return redacted
    if isinstance(payload, list):
        return [redact_lifecycle_payload(item) for item in payload]
    if isinstance(payload, str):
        lowered = payload.lower()
        if any(marker in lowered for marker in _REMOVED_TEXT_MARKERS):
            return "[REMOVED]"
        if any(marker in lowered for marker in ("sk-", "xoxb-", "ghp_", "-----begin")):
            return "[REDACTED]"
    return payload


def sensitive_metadata_paths(payload: Any, prefix: str = "metadata") -> list[str]:
    """Detect metadata paths that should be reviewed for redaction."""

    paths: list[str] = []
    if isinstance(payload, dict):
        for key, value in payload.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            lowered = str(key).lower().replace("-", "_")
            if any(part in lowered for part in _SECRET_KEY_PARTS):
                paths.append(path)
            paths.extend(sensitive_metadata_paths(value, path))
    elif isinstance(payload, list):
        for index, item in enumerate(payload):
            paths.extend(sensitive_metadata_paths(item, f"{prefix}[{index}]"))
    return paths


__all__ = ["redact_lifecycle_payload", "sensitive_metadata_paths"]
