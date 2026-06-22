"""Dialogue content redaction before persistence."""

from __future__ import annotations

import re

_SECRET_VALUE_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"(?i)(api[_-]?key|token|password|secret)\s*[:=]\s*([^\s,;]+)"),
    re.compile(r"(?i)authorization\s*[:=]\s*bearer\s+([^\s,;]+)"),
    re.compile(r"(?i)sk-[a-z0-9_-]{8,}"),
    re.compile(r"(?i)ghp_[a-z0-9_]{8,}"),
    re.compile(r"(?i)xoxb-[a-z0-9-]{8,}"),
    re.compile(r"(?is)-----begin private key-----.*?-----end private key-----"),
)
_DROP_LINE_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(
        r"(?i)^\s*(chain[_ -]?of[_ -]?thought|hidden[_ -]?reasoning|raw[_ -]?prompt)\s*:.*$"
    ),
)
_INLINE_MARKERS: tuple[re.Pattern[str], ...] = (
    re.compile(r"(?i)chain[_ -]?of[_ -]?thought"),
    re.compile(r"(?i)hidden[_ -]?reasoning"),
    re.compile(r"(?i)raw[_ -]?prompt"),
)


def redact_message_content(content: str) -> tuple[str, bool]:
    """Redact secrets and hidden-reasoning markers from dialogue content."""

    redacted = content.replace("\r\n", "\n").replace("\r", "\n")
    changed = redacted != content
    kept_lines: list[str] = []
    for line in redacted.split("\n"):
        if any(pattern.search(line) for pattern in _DROP_LINE_PATTERNS):
            changed = True
            continue
        kept_lines.append(line)
    redacted = "\n".join(kept_lines)
    for pattern in _SECRET_VALUE_PATTERNS:
        new_value = pattern.sub(_redact_match, redacted)
        changed = changed or new_value != redacted
        redacted = new_value
    for marker in _INLINE_MARKERS:
        new_value = marker.sub("[REDACTED]", redacted)
        changed = changed or new_value != redacted
        redacted = new_value
    cleaned = redacted.strip()
    if not cleaned:
        cleaned = "[REDACTED]"
        changed = True
    return cleaned, changed


def _redact_match(match: re.Match[str]) -> str:
    if len(match.groups()) >= 2:
        return f"{match.group(1)}=[REDACTED]"
    return "[REDACTED]"
