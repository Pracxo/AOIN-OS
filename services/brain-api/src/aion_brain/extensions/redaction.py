"""Redaction helpers for extension registry metadata."""

from __future__ import annotations

from typing import Any

from aion_brain.contracts.model_outputs import reject_hidden_or_secret_text

_SECRET_KEY_MARKERS = {
    "api_key",
    "apikey",
    "authorization",
    "bearer",
    "credential",
    "password",
    "private_key",
    "raw_prompt",
    "secret",
    "token",
}
_HIDDEN_KEY_MARKERS = {
    "chain_of_thought",
    "chain-of-thought",
    "hidden_reasoning",
    "hidden-reasoning",
    "raw_prompt",
}
_EXECUTABLE_KEY_MARKERS = {
    "binary",
    "code_payload",
    "dockerfile",
    "entrypoint",
    "executable",
    "hook",
    "package_bytes",
    "script",
    "source_code",
    "subprocess",
}


def redact_extension_payload(value: Any) -> Any:
    """Return a redacted copy of extension metadata."""

    if isinstance(value, dict):
        redacted: dict[str, Any] = {}
        for key, nested in value.items():
            lowered = str(key).lower().replace("-", "_")
            if _is_redacted_key(lowered):
                redacted[str(key)] = "[REDACTED]"
                continue
            redacted[str(key)] = redact_extension_payload(nested)
        return redacted
    if isinstance(value, list):
        return [redact_extension_payload(item) for item in value]
    if isinstance(value, str):
        try:
            reject_hidden_or_secret_text(value, "extension payload")
        except ValueError:
            return "[REDACTED]"
    return value


def reject_executable_payload(value: Any) -> None:
    """Reject executable payload keys."""

    if isinstance(value, dict):
        for key, nested in value.items():
            lowered = str(key).lower().replace("-", "_")
            if lowered in _EXECUTABLE_KEY_MARKERS:
                raise ValueError("extension metadata must not include executable payload fields")
            reject_executable_payload(nested)
    elif isinstance(value, list):
        for item in value:
            reject_executable_payload(item)


def _is_redacted_key(lowered: str) -> bool:
    return any(marker in lowered for marker in _SECRET_KEY_MARKERS | _HIDDEN_KEY_MARKERS)


__all__ = ["redact_extension_payload", "reject_executable_payload"]
