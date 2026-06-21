"""Deterministic public statement splitter."""

from __future__ import annotations

import re

_SENTENCE_BOUNDARY_RE = re.compile(r"(?<=[.!?])\s+")
_BULLET_RE = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+")
_STATUS_WORDS = {
    "blocked",
    "completed",
    "failed",
    "passed",
    "ready",
    "warning",
}


class StatementSplitter:
    """Split public text into candidate factual statements without inference."""

    def split(self, text: str, max_statements: int) -> list[str]:
        """Return at most `max_statements` deterministic statements."""

        if max_statements <= 0:
            return []
        statements: list[str] = []
        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            if _BULLET_RE.match(line):
                candidates = [_BULLET_RE.sub("", line).strip()]
            else:
                candidates = [part.strip() for part in _SENTENCE_BOUNDARY_RE.split(line)]
            for candidate in candidates:
                normalized = candidate.strip(" \t\r\n")
                if not normalized:
                    continue
                if _too_short(normalized):
                    continue
                statements.append(normalized)
                if len(statements) >= max_statements:
                    return statements
        return statements


def _too_short(statement: str) -> bool:
    words = [word for word in re.split(r"\s+", statement) if word]
    if len(words) >= 4:
        return False
    lowered = statement.lower()
    return not any(word in lowered for word in _STATUS_WORDS)


__all__ = ["StatementSplitter"]
