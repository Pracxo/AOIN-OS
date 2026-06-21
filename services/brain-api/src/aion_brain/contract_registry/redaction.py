"""Redaction helpers for contract registry snapshots."""

from __future__ import annotations

import hashlib
from typing import Any

SECRET_KEY_PARTS = {
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
HIDDEN_KEY_PARTS = {
    "chain_of_thought",
    "chain-of-thought",
    "hidden_reasoning",
    "hidden-reasoning",
    "private_reasoning",
    "raw_prompt",
    "prompt_text",
}
SECRET_VALUE_MARKERS = ("sk-", "xoxb-", "ghp_", "-----begin private key-----")
HIDDEN_VALUE_MARKERS = (
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
REDACTED = "[redacted]"


def redact_contract_payload(value: Any) -> Any:
    """Return a deterministic, safe copy of contract metadata or schema data."""

    if isinstance(value, dict):
        redacted: dict[str, Any] = {}
        for key, nested in sorted(value.items(), key=lambda item: str(item[0])):
            normalized = _normalize_key(str(key))
            if _is_sensitive_key(normalized):
                redacted[_redacted_key(normalized)] = REDACTED
                continue
            redacted[str(key)] = redact_contract_payload(nested)
        return redacted
    if isinstance(value, list):
        return [redact_contract_payload(item) for item in value]
    if isinstance(value, str):
        lowered = value.lower()
        if _is_sensitive_key(_normalize_key(value)):
            return REDACTED
        if any(marker in lowered for marker in SECRET_VALUE_MARKERS + HIDDEN_VALUE_MARKERS):
            return REDACTED
        return value
    return value


def contains_disallowed_domain_term(value: Any) -> bool:
    """Detect vertical-domain terms that do not belong in Brain core contract types."""

    blocked = (
        "finance",
        "trading",
        "legal",
        "healthcare",
        "medical",
        "procurement",
        "payments",
        "payroll",
        "hr.",
        "human_resources",
    )
    text = _flatten(value).lower()
    return any(term in text for term in blocked)


def _is_sensitive_key(normalized: str) -> bool:
    return any(part in normalized for part in SECRET_KEY_PARTS | HIDDEN_KEY_PARTS)


def _normalize_key(value: str) -> str:
    return value.lower().replace("-", "_").replace(" ", "_")


def _redacted_key(value: str) -> str:
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()[:12]
    return f"redacted_{digest}"


def _flatten(value: Any) -> str:
    if isinstance(value, dict):
        return " ".join(f"{key} {_flatten(nested)}" for key, nested in value.items())
    if isinstance(value, list):
        return " ".join(_flatten(item) for item in value)
    return str(value)


__all__ = ["contains_disallowed_domain_term", "redact_contract_payload"]
