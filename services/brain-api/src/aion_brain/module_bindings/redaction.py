"""Redaction helpers for module binding metadata."""

from __future__ import annotations

from typing import Any

from aion_brain.model_outputs.redaction import redact_output_payload

_REMOVED_KEYS = {
    "chain_of_thought",
    "chain-of-thought",
    "hidden_reasoning",
    "private_reasoning",
    "raw_prompt",
}


def redact_binding_payload(value: dict[str, Any]) -> dict[str, Any]:
    """Return a redacted payload without preserving removed raw values."""

    scrubbed = _remove_protected_keys(value)
    redacted, _findings = redact_output_payload(scrubbed)
    return redacted


def _remove_protected_keys(value: Any) -> Any:
    if isinstance(value, dict):
        clean: dict[str, Any] = {}
        for key, nested in value.items():
            lowered = str(key).lower().replace("-", "_")
            if lowered in _REMOVED_KEYS:
                clean[f"removed_field_{len(clean) + 1}"] = "[removed]"
                continue
            clean[str(key)] = _remove_protected_keys(nested)
        return clean
    if isinstance(value, list):
        return [_remove_protected_keys(item) for item in value]
    return value


__all__ = ["redact_binding_payload"]
