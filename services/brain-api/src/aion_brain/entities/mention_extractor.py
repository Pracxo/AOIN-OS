"""Deterministic entity mention extraction."""

from __future__ import annotations

import re
from collections.abc import Iterable
from typing import cast

from aion_brain.contracts.entities import (
    EntityExtractMentionsRequest,
    EntityMentionCreateRequest,
    EntityMentionType,
)
from aion_brain.entities.normalizer import normalize_entity_name

_BRACKET_PATTERN = re.compile(r"\[\[([^\[\]\n]{2,120})\]\]")
_QUOTE_PATTERN = re.compile(r'"([^"\n]{2,120})"|\'([^\'\n]{2,120})\'')
_IDENTIFIER_PATTERN = re.compile(r"\b[a-zA-Z][a-zA-Z0-9]*(?:[._:/-][a-zA-Z0-9]+){1,5}\b")
_TITLE_PATTERN = re.compile(r"\b[A-Z][a-z0-9]+(?:\s+[A-Z][a-z0-9]+){0,4}\b")
_TITLE_STOPWORDS = {
    "how",
    "please",
    "remember",
    "retrieve",
    "use",
    "what",
    "when",
    "where",
    "why",
}


class EntityMentionExtractor:
    """Extract generic entity-like references without domain classification."""

    def extract(self, request: EntityExtractMentionsRequest) -> list[EntityMentionCreateRequest]:
        """Return stable mentions in source order."""
        seen: set[str] = set()
        mentions: list[EntityMentionCreateRequest] = []
        for text, start, end, confidence, mention_type in _candidate_spans(request.text):
            normalized = normalize_entity_name(text)
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            mentions.append(
                EntityMentionCreateRequest(
                    trace_id=request.trace_id,
                    source_type=request.source_type,
                    source_id=request.source_id,
                    mention_text=text.strip(),
                    mention_type=cast(EntityMentionType, mention_type),
                    start_char=start,
                    end_char=end,
                    confidence=confidence,
                    owner_scope=request.owner_scope,
                    metadata={"extractor": "deterministic_v0"},
                )
            )
            if len(mentions) >= request.max_mentions:
                break
        return mentions


def _candidate_spans(text: str) -> Iterable[tuple[str, int, int, float, str]]:
    for match in _BRACKET_PATTERN.finditer(text):
        yield match.group(1), match.start(1), match.end(1), 0.9, "explicit"
    for match in _QUOTE_PATTERN.finditer(text):
        value = match.group(1) or match.group(2)
        if value:
            yield value, match.start(), match.end(), 0.72, "explicit"
    for match in _IDENTIFIER_PATTERN.finditer(text):
        yield match.group(0), match.start(), match.end(), 0.68, "system_reference"
    for match in _TITLE_PATTERN.finditer(text):
        value = match.group(0)
        if len(value) > 1 and normalize_entity_name(value) not in _TITLE_STOPWORDS:
            yield value, match.start(), match.end(), 0.58, "inferred_from_text"
