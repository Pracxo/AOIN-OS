"""Redaction and safety checks for provider hardening metadata."""

from __future__ import annotations

from typing import Any

SECRET_KEY_PARTS = {
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
RAW_PROMPT_KEYS = {"raw_prompt", "prompt", "prompt_body", "messages", "system_prompt"}
HIDDEN_REASONING_KEYS = {"hidden_reasoning", "chain_of_thought", "chain-of-thought"}
TOOL_INTENT_KEYS = {"tool_call", "tool_calls", "execute_tool", "capability_invoke"}
SECRET_VALUE_MARKERS = ("sk-", "xoxb-", "ghp_", "-----begin private key-----")


def redact_provider_payload(payload: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    """Return a recursively redacted copy and the blocked field paths."""

    blocked: list[str] = []
    redacted = _redact(payload, "", blocked)
    return redacted if isinstance(redacted, dict) else {}, blocked


def detect_provider_safety_issues(payload: dict[str, Any]) -> list[dict[str, str]]:
    """Detect prompt egress issues without raising or storing raw content."""

    issues: list[dict[str, str]] = []
    _detect(payload, "", issues)
    return issues


def payload_has_tool_intent(payload: dict[str, Any]) -> bool:
    """Return whether payload appears to request tool execution."""

    return any(
        issue["type"] == "tool_intent_guard_missing"
        for issue in detect_provider_safety_issues(payload)
    )


def _redact(value: object, path: str, blocked: list[str]) -> object:
    if isinstance(value, dict):
        result: dict[str, object] = {}
        for key, nested in value.items():
            key_text = str(key)
            lowered = key_text.lower().replace("-", "_")
            nested_path = f"{path}.{key_text}" if path else key_text
            if _is_blocked_key(lowered):
                blocked.append(nested_path)
                result[f"redacted_field_{len(blocked)}"] = "[REDACTED]"
            else:
                result[key_text] = _redact(nested, nested_path, blocked)
        return result
    if isinstance(value, list):
        return [_redact(item, f"{path}[]", blocked) for item in value]
    if isinstance(value, str) and _is_blocked_value(value):
        blocked.append(path or "value")
        return "[REDACTED]"
    if isinstance(value, str) and _contains_hidden_reasoning(value):
        blocked.append(path or "value")
        return "[REDACTED]"
    return value


def _detect(value: object, path: str, issues: list[dict[str, str]]) -> None:
    if isinstance(value, dict):
        untrusted_context = bool(value.get("untrusted_context"))
        marked_trusted = str(value.get("context_trust", "")).lower() == "trusted"
        if untrusted_context and marked_trusted:
            issues.append(
                {
                    "type": "generic",
                    "field": path or "prompt_summary",
                    "reason": "untrusted context is marked trusted",
                }
            )
        for key, nested in value.items():
            key_text = str(key)
            lowered = key_text.lower().replace("-", "_")
            nested_path = f"{path}.{key_text}" if path else key_text
            if lowered in RAW_PROMPT_KEYS:
                issues.append(
                    {
                        "type": "raw_prompt_detected",
                        "field": nested_path,
                        "reason": "raw prompt content is not allowed in egress previews",
                    }
                )
            elif lowered in HIDDEN_REASONING_KEYS:
                issues.append(
                    {
                        "type": "hidden_reasoning_detected",
                        "field": nested_path,
                        "reason": "hidden reasoning is not allowed in egress previews",
                    }
                )
            elif lowered in TOOL_INTENT_KEYS:
                issues.append(
                    {
                        "type": "tool_intent_guard_missing",
                        "field": nested_path,
                        "reason": "tool intent must be blocked before provider egress",
                    }
                )
            elif any(part in lowered for part in SECRET_KEY_PARTS):
                issues.append(
                    {
                        "type": "credential_storage_forbidden",
                        "field": nested_path,
                        "reason": "secret-like field is not allowed",
                    }
                )
            _detect(nested, nested_path, issues)
    elif isinstance(value, list):
        for item in value:
            _detect(item, f"{path}[]", issues)
    elif isinstance(value, str):
        lowered = value.lower()
        if "hidden reasoning" in lowered or "chain-of-thought" in lowered:
            issues.append(
                {
                    "type": "hidden_reasoning_detected",
                    "field": path or "value",
                    "reason": "hidden reasoning is not allowed",
                }
            )
        elif _is_blocked_value(value):
            issues.append(
                {
                    "type": "credential_storage_forbidden",
                    "field": path or "value",
                    "reason": "secret-like value is not allowed",
                }
            )


def _is_blocked_key(lowered: str) -> bool:
    return (
        lowered in RAW_PROMPT_KEYS
        or lowered in HIDDEN_REASONING_KEYS
        or any(part in lowered for part in SECRET_KEY_PARTS)
    )


def _is_blocked_value(value: str) -> bool:
    lowered = value.lower()
    return any(marker in lowered for marker in SECRET_VALUE_MARKERS)


def _contains_hidden_reasoning(value: str) -> bool:
    lowered = value.lower()
    return "hidden reasoning" in lowered or "chain-of-thought" in lowered


__all__ = [
    "detect_provider_safety_issues",
    "payload_has_tool_intent",
    "redact_provider_payload",
]
