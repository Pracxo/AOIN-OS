"""Deterministic prompt redaction for model gateway requests."""

import re
from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from aion_brain.contracts.model_gateway import PromptRedactionRecord
from aion_brain.contracts.reasoning import PromptPacket

_PRIVATE_KEY_PATTERN = (
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----"
)

_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("private_key_like", re.compile(_PRIVATE_KEY_PATTERN, re.DOTALL)),
    ("bearer_token_like", re.compile(r"(?i)(bearer\s+)[a-z0-9._~+/=-]{12,}")),
    ("api_key_like", re.compile(r"(?i)(api[_-]?key\s*[:=]\s*)[^\s,;]+")),
    ("password_like", re.compile(r"(?i)(password\s*[:=]\s*)[^\s,;]+")),
    ("long_secret_like", re.compile(r"\b[a-zA-Z0-9_\-]{32,}\b")),
)


class PromptRedactor:
    """Inspect and redact secret-like prompt content without external calls."""

    def __init__(self, *, block_on_secret: bool = True) -> None:
        self._block_on_secret = block_on_secret

    def inspect(self, prompt: PromptPacket) -> PromptRedactionRecord:
        """Inspect a prompt packet and return a redaction ledger record."""
        findings = _scan(prompt.model_dump(mode="python"))
        blocked = self._block_on_secret and bool(findings)
        return PromptRedactionRecord(
            redaction_id=f"redaction-{uuid4().hex}",
            trace_id=prompt.trace_id,
            reasoning_id=None,
            prompt_id=prompt.prompt_id,
            redaction_count=sum(findings.values()),
            redaction_types=sorted(findings),
            blocked=blocked,
            reason="secret_like_content_detected" if blocked else None,
            created_at=datetime.now(UTC),
        )

    def redact(self, prompt: PromptPacket) -> tuple[PromptPacket, PromptRedactionRecord]:
        """Return a redacted copy of the prompt and its ledger record."""
        record = self.inspect(prompt)
        if record.blocked or record.redaction_count == 0:
            return prompt, record
        redacted = prompt.model_copy(
            update={
                "goal": _redact_value(prompt.goal),
                "system_instructions": [
                    _redact_value(item) for item in prompt.system_instructions
                ],
                "context_items": [
                    _redact_value(item) for item in prompt.context_items
                ],
                "constraints": [_redact_value(item) for item in prompt.constraints],
                "requested_output_schema": _redact_value(prompt.requested_output_schema),
            }
        )
        return redacted, record


def _scan(value: object) -> dict[str, int]:
    findings: dict[str, int] = {}
    for text in _walk_strings(value):
        for redaction_type, pattern in _PATTERNS:
            count = len(pattern.findall(text))
            if count:
                findings[redaction_type] = findings.get(redaction_type, 0) + count
    return findings


def _walk_strings(value: object) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, Mapping):
        strings: list[str] = []
        for key, nested in value.items():
            strings.extend(_walk_strings(str(key)))
            strings.extend(_walk_strings(nested))
        return strings
    if isinstance(value, list | tuple):
        strings = []
        for item in value:
            strings.extend(_walk_strings(item))
        return strings
    return []


def _redact_value(value: Any) -> Any:
    if isinstance(value, str):
        redacted = value
        for redaction_type, pattern in _PATTERNS:
            if redaction_type in {"api_key_like", "password_like", "bearer_token_like"}:
                redacted = pattern.sub(lambda match: f"{match.group(1)}[REDACTED]", redacted)
            else:
                redacted = pattern.sub("[REDACTED]", redacted)
        return redacted
    if isinstance(value, dict):
        return {key: _redact_value(nested) for key, nested in value.items()}
    if isinstance(value, list):
        return [_redact_value(item) for item in value]
    return value
