"""Redaction helpers for module mock runtime payloads."""

from __future__ import annotations

from typing import Any

_REDACTED = "[redacted]"
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
_RAW_PROMPT_KEYS = {"raw_prompt", "prompt_raw", "system_prompt", "developer_prompt"}
_HIDDEN_KEYS = {"chain_of_thought", "hidden_reasoning", "private_reasoning"}
_EXECUTABLE_KEYS = {
    "code",
    "command",
    "entrypoint",
    "exec",
    "execute",
    "function_body",
    "import",
    "script",
    "shell",
    "subprocess",
}
_HIDDEN_VALUE_MARKERS = (
    "chain-of-thought",
    "chain_of_thought",
    "hidden reasoning",
    "private reasoning",
    "raw prompt",
    "system prompt:",
    "developer prompt:",
)
_SECRET_VALUE_MARKERS = ("sk-", "xoxb-", "ghp_", "-----begin private key-----")


def redact_module_mock_payload(value: Any) -> Any:
    """Return a deterministic redacted copy of a mock payload."""

    if isinstance(value, dict):
        redacted: dict[str, Any] = {}
        for key, nested in sorted(value.items(), key=lambda item: str(item[0])):
            lowered = str(key).lower().replace("-", "_")
            if _is_sensitive_key(lowered) or lowered in _RAW_PROMPT_KEYS or lowered in _HIDDEN_KEYS:
                redacted[str(key)] = _REDACTED
            elif lowered in _EXECUTABLE_KEYS:
                redacted[str(key)] = _REDACTED
            else:
                redacted[str(key)] = redact_module_mock_payload(nested)
        return redacted
    if isinstance(value, list):
        return [redact_module_mock_payload(item) for item in value]
    if isinstance(value, str):
        lowered = value.lower()
        if any(marker in lowered for marker in (*_HIDDEN_VALUE_MARKERS, *_SECRET_VALUE_MARKERS)):
            return _REDACTED
        return value
    return value


def _is_sensitive_key(key: str) -> bool:
    return any(part in key for part in _SECRET_KEY_PARTS)


__all__ = ["redact_module_mock_payload"]
