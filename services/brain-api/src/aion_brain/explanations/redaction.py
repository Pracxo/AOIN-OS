"""Public-safe redaction helpers for explanation records."""

from __future__ import annotations

import re
from typing import Any

from aion_brain.contracts.explanations import (
    contains_hidden_reasoning_marker as _contract_contains_hidden_reasoning_marker,
)
from aion_brain.contracts.explanations import (
    contains_raw_prompt_marker as _contract_contains_raw_prompt_marker,
)

_SECRET_KEY_PARTS = {
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
_SECRET_VALUE_PATTERNS = (
    re.compile(r"sk-[A-Za-z0-9_\-]+"),
    re.compile(r"ghp_[A-Za-z0-9_\-]+"),
    re.compile(r"xoxb-[A-Za-z0-9_\-]+"),
    re.compile(r"-----BEGIN PRIVATE KEY-----.*?-----END PRIVATE KEY-----", re.I | re.S),
)


def redact_explanation_text(text: str) -> tuple[str, dict[str, Any]]:
    """Remove hidden reasoning, raw prompt markers, and obvious secret values."""

    redaction_count = 0
    lines: list[str] = []
    for line in text.splitlines() or [text]:
        if _contract_contains_hidden_reasoning_marker(line):
            lines.append("[redacted_hidden_reasoning]")
            redaction_count += 1
            continue
        if _contract_contains_raw_prompt_marker(line):
            lines.append("[redacted_raw_prompt]")
            redaction_count += 1
            continue
        clean = line
        for pattern in _SECRET_VALUE_PATTERNS:
            clean, count = pattern.subn("[redacted_secret]", clean)
            redaction_count += count
        lines.append(clean)
    redacted = "\n".join(lines)
    return redacted, {
        "redacted": redaction_count > 0,
        "redaction_count": redaction_count,
        "removed_count": 0,
        "field_paths": [],
        "removed_field_paths": [],
    }


def sanitize_explanation_payload(payload: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    """Return a payload with secret-like and hidden fields removed."""

    metadata: dict[str, Any] = {
        "redacted": False,
        "redaction_count": 0,
        "removed_count": 0,
        "field_paths": [],
        "removed_field_paths": [],
    }
    clean = _sanitize_value(payload, "", metadata)
    return (clean if isinstance(clean, dict) else {}, metadata)


def contains_hidden_reasoning_marker_text(text: str) -> bool:
    """Compatibility wrapper for hidden reasoning detection."""

    return _contract_contains_hidden_reasoning_marker(text)


def contains_raw_prompt_marker_text(text: str) -> bool:
    """Compatibility wrapper for raw prompt detection."""

    return _contract_contains_raw_prompt_marker(text)


def _sanitize_value(value: Any, path: str, metadata: dict[str, Any]) -> Any:
    if isinstance(value, dict):
        clean: dict[str, Any] = {}
        for key, item in value.items():
            child_path = f"{path}.{key}" if path else str(key)
            if _is_secret_key(str(key)) or _contract_contains_raw_prompt_marker(str(key)):
                metadata["redacted"] = True
                metadata["removed_count"] += 1
                metadata["removed_field_paths"].append(child_path)
                continue
            clean[key] = _sanitize_value(item, child_path, metadata)
        return clean
    if isinstance(value, list):
        return [
            _sanitize_value(item, f"{path}.{index}", metadata) for index, item in enumerate(value)
        ]
    if isinstance(value, str):
        redacted, text_metadata = redact_explanation_text(value)
        if text_metadata["redacted"]:
            metadata["redacted"] = True
            metadata["redaction_count"] += int(text_metadata["redaction_count"])
            metadata["field_paths"].append(path)
        return redacted
    return value


def _is_secret_key(key: str) -> bool:
    lowered = key.lower().replace("-", "_")
    return any(part in lowered for part in _SECRET_KEY_PARTS)


contains_hidden_reasoning_marker = contains_hidden_reasoning_marker_text
contains_raw_prompt_marker = contains_raw_prompt_marker_text

__all__ = [
    "contains_hidden_reasoning_marker",
    "contains_raw_prompt_marker",
    "redact_explanation_text",
    "sanitize_explanation_payload",
]
