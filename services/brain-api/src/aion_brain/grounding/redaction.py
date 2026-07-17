"""Grounding redaction helpers for public source-attribution records."""

from __future__ import annotations

import re
from typing import Any

_SECRET_KEY_PARTS = (
    "api_key",
    "apikey",
    "authorization",
    "bearer",
    "credential",
    "password",
    "private_key",
    "secret",
    "token",
)
_SECRET_VALUE_RE = re.compile(
    r"("
    r"sk-[A-Za-z0-9_\-]{8,}|"
    r"xoxb-[A-Za-z0-9_\-]{8,}|"
    r"ghp_[A-Za-z0-9_]{8,}|"
    r"-----BEGIN " r"PRIVATE KEY-----.*?-----END " r"PRIVATE KEY-----"
    r")",
    re.IGNORECASE | re.DOTALL,
)
_HIDDEN_LINE_RE = re.compile(
    r"(?im)^\s*("
    r"chain[-_ ]of[-_ ]thought|"
    r"hidden[-_ ]reasoning|"
    r"private reasoning|"
    r"raw[-_ ]prompt|"
    r"system prompt|"
    r"developer prompt"
    r")\s*:.*$"
)


def redact_text(value: str) -> str:
    """Remove hidden reasoning/raw-prompt lines and redact obvious secret values."""

    without_hidden = _HIDDEN_LINE_RE.sub("[redacted]", value)
    return _SECRET_VALUE_RE.sub("[redacted]", without_hidden)


def sanitize_payload(value: Any) -> Any:
    """Return a copy with secret-like keys removed and string values redacted."""

    if isinstance(value, dict):
        safe: dict[str, Any] = {}
        for key, item in value.items():
            lowered = str(key).lower()
            if any(part in lowered for part in _SECRET_KEY_PARTS) or "raw_prompt" in lowered:
                safe[str(key)] = "[redacted]"
                continue
            safe[str(key)] = sanitize_payload(item)
        return safe
    if isinstance(value, list):
        return [sanitize_payload(item) for item in value]
    if isinstance(value, str):
        return redact_text(value)
    return value


__all__ = ["redact_text", "sanitize_payload"]
