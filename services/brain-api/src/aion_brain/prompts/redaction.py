"""Prompt redaction helpers for safe previews and manifests."""

from __future__ import annotations

import re
from typing import Any

from aion_brain.contracts.prompts import PromptSection

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
_SECRET_HINTS = ("api_key", "apikey", "password", "private_key", "secret", "token")
_HIDDEN_MARKERS = (
    "chain-of-thought",
    "chain_of_thought",
    "hidden reasoning",
    "hidden_reasoning",
    "private reasoning",
    "raw prompt",
)


def redact_prompt_text(text: str) -> tuple[str, dict[str, Any]]:
    """Return redacted text and redaction metadata."""

    hidden_count = len(_HIDDEN_LINE_RE.findall(text))
    without_hidden = _HIDDEN_LINE_RE.sub("[redacted]", text)
    secret_count = len(_SECRET_VALUE_RE.findall(without_hidden))
    redacted = _SECRET_VALUE_RE.sub("[redacted]", without_hidden)
    return redacted, {
        "redacted": bool(hidden_count or secret_count),
        "hidden_marker_count": hidden_count,
        "sensitive_value_count": secret_count,
    }


def redact_prompt_section(section: PromptSection) -> PromptSection:
    """Return a copy of a section with safe redacted content."""

    content, metadata = redact_prompt_text(section.content)
    return section.model_copy(
        update={
            "content": content,
            "redacted": section.redacted or bool(metadata["redacted"]),
            "metadata": {**section.metadata, "redaction": metadata},
        }
    )


def contains_hidden_reasoning_marker(text: str) -> bool:
    """Return true when text asks for or stores hidden reasoning/raw prompts."""

    lowered = text.lower()
    return any(marker in lowered for marker in _HIDDEN_MARKERS)


def contains_secret_like_text(text: str) -> bool:
    """Return true for obvious secret values or direct secret key labels."""

    lowered = text.lower()
    return bool(_SECRET_VALUE_RE.search(text)) or any(hint in lowered for hint in _SECRET_HINTS)


def sanitize_prompt_payload(value: Any) -> Any:
    """Recursively redact secret-like keys and text values."""

    if isinstance(value, dict):
        safe: dict[str, Any] = {}
        for key, item in value.items():
            lowered = str(key).lower().replace("-", "_")
            if any(hint in lowered for hint in _SECRET_HINTS) or "raw_prompt" in lowered:
                safe[str(key)] = "[redacted]"
                continue
            safe[str(key)] = sanitize_prompt_payload(item)
        return safe
    if isinstance(value, list):
        return [sanitize_prompt_payload(item) for item in value]
    if isinstance(value, str):
        return redact_prompt_text(value)[0]
    return value


__all__ = [
    "contains_hidden_reasoning_marker",
    "contains_secret_like_text",
    "redact_prompt_section",
    "redact_prompt_text",
    "sanitize_prompt_payload",
]
