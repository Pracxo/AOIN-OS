"""Redaction helpers for read-only local session surfaces."""

from __future__ import annotations

from typing import Any

REDACTED = "[redacted]"

_SENSITIVE_KEY_PARTS = {
    "api_key",
    "apikey",
    "authorization",
    "bearer",
    "chain_of_thought",
    "credential",
    "hidden_reasoning",
    "password",
    "private_key",
    "provider_payload",
    "raw_model_payload",
    "raw_prompt",
    "secret",
    "token",
}
_SENSITIVE_TEXT_MARKERS = (
    "sk-",
    "xoxb-",
    "ghp_",
    "-----begin private key-----",
    "raw_prompt",
    "raw prompt",
    "hidden_reasoning",
    "hidden reasoning",
    "chain-of-thought",
    "chain_of_thought",
)


def scrub_local_session_payload(
    value: Any,
    *,
    findings: list[dict[str, object]] | None = None,
) -> Any:
    """Return a copy with unsafe session/auth material removed."""
    if isinstance(value, dict):
        redacted: dict[str, Any] = {}
        for index, (key, nested) in enumerate(value.items()):
            if _is_sensitive_key(str(key), nested):
                if findings is not None:
                    findings.append({"finding": "unsafe_field_removed", "field_index": index})
                continue
            redacted[str(key)] = scrub_local_session_payload(nested, findings=findings)
        return redacted
    if isinstance(value, list):
        return [scrub_local_session_payload(item, findings=findings) for item in value]
    if isinstance(value, str):
        if _is_sensitive_text(value):
            if findings is not None:
                findings.append({"finding": "unsafe_text_redacted"})
            return REDACTED
        return value
    return value


def local_session_payload_has_unsafe_content(value: Any) -> bool:
    """Return true when a payload contains unsafe local session material."""
    if isinstance(value, dict):
        return any(
            _is_sensitive_key(str(key), nested)
            or local_session_payload_has_unsafe_content(nested)
            for key, nested in value.items()
        )
    if isinstance(value, list):
        return any(local_session_payload_has_unsafe_content(item) for item in value)
    if isinstance(value, str):
        return _is_sensitive_text(value)
    return False


def _is_sensitive_key(value: str, nested: Any) -> bool:
    normalized = value.lower().replace("-", "_")
    if "timeout" in normalized:
        return False
    if any(
        normalized == allowed
        for allowed in (
            "token_issued",
            "cookie_issued",
            "credential_backed",
            "credential_material_present",
            "cookie_values_present",
            "credentials_enabled",
            "tokens_enabled",
            "cookies_enabled",
        )
    ) and _is_disabled_or_absent_marker(nested):
        return False
    return any(part in normalized for part in _SENSITIVE_KEY_PARTS)


def _is_sensitive_text(value: str) -> bool:
    lowered = value.lower()
    return any(marker in lowered for marker in _SENSITIVE_TEXT_MARKERS)


def _is_disabled_or_absent_marker(value: Any) -> bool:
    if value is False:
        return True
    if isinstance(value, str):
        return value.lower() in {"absent", "disabled", "false", "none", "not_present"}
    return False


__all__ = [
    "REDACTED",
    "local_session_payload_has_unsafe_content",
    "scrub_local_session_payload",
]
