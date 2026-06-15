"""Audit payload redaction helpers."""

from __future__ import annotations

from typing import Any

SENSITIVE_KEY_PARTS = {
    "password",
    "secret",
    "token",
    "api_key",
    "apikey",
    "private_key",
    "credential",
    "authorization",
    "bearer",
    "raw_prompt",
}
REMOVED_KEY_PARTS = {"chain_of_thought", "hidden_reasoning"}


def contains_sensitive_key(key: str) -> bool:
    """Return whether a key should never store raw values."""
    normalized = key.lower().replace("-", "_")
    return normalized in REMOVED_KEY_PARTS or any(
        part in normalized for part in SENSITIVE_KEY_PARTS
    )


def strip_chain_of_thought(value: dict[str, Any]) -> dict[str, Any]:
    """Return a copy with hidden reasoning fields removed."""
    stripped = _redact_value(value, [], redact_sensitive=False)
    return dict(stripped[0]) if isinstance(stripped[0], dict) else {}


def redact_audit_payload(payload: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    """Redact one audit payload and return redaction metadata."""
    redacted, metadata = _redact_value(payload, [], redact_sensitive=True)
    metadata["redacted"] = bool(metadata["redaction_count"] or metadata["removed_count"])
    return dict(redacted) if isinstance(redacted, dict) else {}, metadata


def _redact_value(
    value: Any,
    path: list[str],
    *,
    redact_sensitive: bool,
) -> tuple[Any, dict[str, Any]]:
    metadata: dict[str, Any] = {
        "redaction_count": 0,
        "removed_count": 0,
        "field_paths": [],
        "removed_field_paths": [],
    }
    if isinstance(value, dict):
        result: dict[str, Any] = {}
        for key, item in value.items():
            normalized = str(key).lower().replace("-", "_")
            next_path = [*path, str(key)]
            dotted = ".".join(next_path)
            if normalized in REMOVED_KEY_PARTS:
                metadata["removed_count"] += 1
                metadata["removed_field_paths"].append(dotted)
                continue
            if contains_sensitive_key(str(key)) and redact_sensitive:
                result[str(key)] = "[REDACTED]"
                metadata["redaction_count"] += 1
                metadata["field_paths"].append(dotted)
                continue
            child, child_metadata = _redact_value(
                item,
                next_path,
                redact_sensitive=redact_sensitive,
            )
            result[str(key)] = child
            _merge_metadata(metadata, child_metadata)
        return result, metadata
    if isinstance(value, list):
        result_list = []
        for index, item in enumerate(value):
            child, child_metadata = _redact_value(
                item,
                [*path, str(index)],
                redact_sensitive=redact_sensitive,
            )
            result_list.append(child)
            _merge_metadata(metadata, child_metadata)
        return result_list, metadata
    return value, metadata


def _merge_metadata(target: dict[str, Any], source: dict[str, Any]) -> None:
    target["redaction_count"] += int(source["redaction_count"])
    target["removed_count"] += int(source["removed_count"])
    target["field_paths"].extend(source["field_paths"])
    target["removed_field_paths"].extend(source["removed_field_paths"])
