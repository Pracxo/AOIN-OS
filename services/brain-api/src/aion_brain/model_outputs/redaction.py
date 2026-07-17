"""Model output redaction helpers."""

from __future__ import annotations

import re
from typing import Any

_SECRET_PATTERNS = (
    re.compile(r"sk-[A-Za-z0-9_\-]{8,}"),
    re.compile(r"ghp_[A-Za-z0-9_]{8,}"),
    re.compile(r"xoxb-[A-Za-z0-9_\-]{8,}"),
    re.compile(r"(?i)(api[_ -]?key|token|password|secret)\s*[:=]\s*[^\s,;]+"),
    re.compile(r"(?i)bearer\s+[A-Za-z0-9_\-.]{8,}"),
    re.compile(r"-----BEGIN " r"PRIVATE KEY-----.*?-----END " r"PRIVATE KEY-----", re.I | re.S),
)
_HIDDEN_PATTERNS = (
    re.compile(r"chain[-_ ]of[-_ ]thought[:\s].*", re.I),
    re.compile(r"hidden reasoning[:\s].*", re.I),
    re.compile(r"private reasoning[:\s].*", re.I),
)
_RAW_PROMPT_PATTERNS = (
    re.compile(r"raw[_ ]prompt[:\s].*", re.I),
    re.compile(r"system prompt[:\s].*", re.I),
    re.compile(r"developer prompt[:\s].*", re.I),
)
_SECRET_KEYS = {
    "api_key",
    "apikey",
    "authorization",
    "credential",
    "password",
    "private_key",
    "raw_prompt",
    "secret",
    "token",
}


def contains_hidden_reasoning_marker(text: str) -> bool:
    """Return true when text appears to expose hidden reasoning."""

    lowered = text.lower()
    return any(
        marker in lowered
        for marker in (
            "chain-of-thought",
            "chain_of_thought",
            "hidden reasoning",
            "hidden_reasoning",
            "private reasoning",
        )
    )


def contains_secret_like_text(text: str) -> bool:
    """Return true when text contains obvious secret-like markers."""

    lowered = text.lower()
    return any(pattern.search(text) for pattern in _SECRET_PATTERNS) or any(
        marker in lowered for marker in ("api key", "password:", "secret:", "bearer ")
    )


def redact_model_output(text: str) -> tuple[str, list[dict[str, Any]]]:
    """Return redacted text and redacted safety findings."""

    findings: list[dict[str, Any]] = []
    redacted = text
    for pattern in _HIDDEN_PATTERNS:
        if pattern.search(redacted):
            findings.append(
                {
                    "code": "protected_reasoning_removed",
                    "severity": "critical",
                    "snippet": "[redacted]",
                }
            )
            redacted = pattern.sub("[protected reasoning removed]", redacted)
    for pattern in _RAW_PROMPT_PATTERNS:
        if pattern.search(redacted):
            findings.append(
                {
                    "code": "protected_prompt_echo_removed",
                    "severity": "high",
                    "snippet": "[redacted]",
                }
            )
            redacted = pattern.sub("[protected prompt echo removed]", redacted)
    for pattern in _SECRET_PATTERNS:
        if pattern.search(redacted):
            findings.append(
                {
                    "code": "secret_like_value_redacted",
                    "severity": "critical",
                    "snippet": "[redacted]",
                }
            )
            redacted = pattern.sub("[secret redacted]", redacted)
    return redacted, findings


def redact_output_payload(value: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Redact secret-like keys and string values from a JSON-like payload."""

    findings: list[dict[str, Any]] = []

    def walk(item: Any) -> Any:
        if isinstance(item, dict):
            clean: dict[str, Any] = {}
            for key, nested in item.items():
                lowered = str(key).lower().replace("-", "_")
                if any(secret_key in lowered for secret_key in _SECRET_KEYS):
                    clean[f"redacted_field_{len(findings) + 1}"] = "[redacted]"
                    findings.append(
                        {
                            "code": "secret_like_key_redacted",
                            "severity": "critical",
                            "key": "[redacted]",
                        }
                    )
                else:
                    clean[key] = walk(nested)
            return clean
        if isinstance(item, list):
            return [walk(nested) for nested in item]
        if isinstance(item, str):
            redacted, nested_findings = redact_model_output(item)
            findings.extend(nested_findings)
            return redacted
        return item

    return walk(value), findings


__all__ = [
    "contains_hidden_reasoning_marker",
    "contains_secret_like_text",
    "redact_model_output",
    "redact_output_payload",
]
