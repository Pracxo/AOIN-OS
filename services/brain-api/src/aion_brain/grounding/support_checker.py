"""Deterministic statement support checker."""

from __future__ import annotations

import re
from typing import Any

from aion_brain.contracts.grounding import GroundingSource
from aion_brain.grounding.hash import normalize_source_text

_STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "has",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "that",
    "the",
    "to",
    "was",
    "were",
    "with",
}


class SupportChecker:
    """Check statements against provided sources with lexical rules only."""

    def check_statement(
        self,
        statement: str,
        sources: list[GroundingSource],
        require_evidence: bool,
        allow_memory_only: bool,
    ) -> dict[str, Any]:
        """Return deterministic support metadata for one statement."""

        best: dict[str, Any] | None = None
        issues: list[str] = []
        for source in sources:
            result = _score_source(statement, source, allow_memory_only)
            if result["issue"]:
                issues.append(str(result["issue"]))
            if best is None or float(result["confidence"]) > float(best["confidence"]):
                best = result
        if best is None:
            return {
                "supported": False,
                "support_level": "none",
                "citation_type": "weak_reference",
                "confidence": 0.0,
                "issues": ["no_candidate_sources"],
                "source_refs": [],
                "grounding_source_ids": [],
            }
        if require_evidence and best["source_type"] not in {"evidence", "evidence_chunk"}:
            issues.append("missing_evidence")
            best = {**best, "supported": False}
        if best["support_level"] == "none":
            best = {**best, "supported": False}
        return {
            "supported": bool(best["supported"]),
            "support_level": best["support_level"],
            "citation_type": best["citation_type"],
            "confidence": best["confidence"],
            "issues": _unique([*issues, *list(best.get("issues", []))]),
            "source_refs": [best["source_id"]] if best.get("source_id") else [],
            "grounding_source_ids": (
                [best["grounding_source_id"]] if best.get("grounding_source_id") else []
            ),
            "source_type": best["source_type"],
        }


def _score_source(
    statement: str,
    source: GroundingSource,
    allow_memory_only: bool,
) -> dict[str, Any]:
    normalized_statement = normalize_source_text(statement).lower()
    normalized_source = normalize_source_text(source.summary).lower()
    overlap = _token_overlap(normalized_statement, normalized_source)
    issue: str | None = None
    support_level = "none"
    confidence = 0.0
    supported = False
    citation_type = "weak_reference"
    if normalized_statement and normalized_statement in normalized_source:
        support_level = "strong"
        confidence = 0.95
        supported = True
        citation_type = "supports_statement"
    elif source.trust_level == "belief_supported" and overlap >= 0.65:
        support_level = "strong"
        confidence = 0.9
        supported = True
        citation_type = "supports_belief"
    elif source.source_type in {"evidence", "evidence_chunk"} and overlap >= 0.45:
        support_level = "moderate"
        confidence = min(0.85, max(0.5, overlap))
        supported = True
        citation_type = "supports_statement"
    elif overlap >= 0.4:
        support_level = "weak"
        confidence = min(0.6, overlap)
        supported = source.source_type != "memory" or allow_memory_only
    if source.source_type == "memory":
        citation_type = "weak_reference"
        if not allow_memory_only:
            issue = "memory_not_truth"
            supported = False
        elif support_level == "none":
            support_level = "weak"
            confidence = max(confidence, 0.35)
    if source.trust_level == "belief_uncertain":
        citation_type = "weak_reference"
        support_level = "weak" if support_level != "none" else "none"
        confidence = min(confidence, 0.55)
    if source.trust_level == "unverified":
        citation_type = "weak_reference"
        confidence = min(confidence, 0.45)
        if confidence > 0:
            support_level = "weak"
    if source.metadata.get("belief_status") == "contradicted" or source.trust_level == "unverified":
        if source.metadata.get("belief_status") == "contradicted":
            issue = "contradicted_support"
            citation_type = "disputed_reference"
            supported = False
    return {
        "supported": supported,
        "support_level": support_level,
        "citation_type": citation_type,
        "confidence": max(0.0, min(1.0, confidence)),
        "issue": issue,
        "issues": [issue] if issue else [],
        "source_type": source.source_type,
        "source_id": source.source_id,
        "grounding_source_id": source.grounding_source_id,
    }


def _token_overlap(statement: str, source: str) -> float:
    statement_tokens = _tokens(statement)
    source_tokens = _tokens(source)
    if not statement_tokens or not source_tokens:
        return 0.0
    return len(statement_tokens & source_tokens) / len(statement_tokens)


def _tokens(value: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-z0-9][a-z0-9_\-]{2,}", value.lower())
        if token not in _STOPWORDS
    }


def _unique(values: list[str]) -> list[str]:
    return list(dict.fromkeys(value for value in values if value))


__all__ = ["SupportChecker"]
