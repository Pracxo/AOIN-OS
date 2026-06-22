"""Deterministic claim extraction."""

from __future__ import annotations

import re

from aion_brain.beliefs.normalizer import is_claim_text_safe
from aion_brain.contracts.beliefs import (
    BeliefClaimCreateRequest,
    BeliefClaimType,
    ClaimExtractionRequest,
    ClaimExtractionResult,
)

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+|\n+")
_COMMAND_STARTERS = {
    "add",
    "build",
    "check",
    "create",
    "delete",
    "do",
    "fix",
    "go",
    "implement",
    "make",
    "please",
    "run",
    "show",
    "update",
}


class ClaimExtractor:
    """Rule-based claim extractor for v0.1."""

    def extract(self, request: ClaimExtractionRequest) -> ClaimExtractionResult:
        """Extract declarative-looking claims without model calls."""
        extracted: list[BeliefClaimCreateRequest] = []
        skipped = 0
        for sentence in _sentences(request.text):
            if len(extracted) >= request.max_claims:
                break
            if not _looks_declarative(sentence):
                skipped += 1
                continue
            if not is_claim_text_safe(sentence):
                skipped += 1
                continue
            extracted.append(
                BeliefClaimCreateRequest(
                    trace_id=request.trace_id,
                    claim_text=sentence,
                    claim_type=_claim_type_for_source(request.source_type),
                    source_type=request.source_type,
                    source_id=request.source_id,
                    owner_scope=request.owner_scope,
                    confidence=_confidence_for_source(request.source_type),
                    metadata={"extracted": True, **request.metadata},
                )
            )
        return ClaimExtractionResult(
            extracted_claims=extracted,
            skipped_count=skipped,
            constraints=["deterministic_extraction_only"],
            metadata={"source_type": request.source_type, "source_id": request.source_id},
        )


def _sentences(text: str) -> list[str]:
    return [
        sentence.strip()
        for sentence in _SENTENCE_SPLIT.split(text.replace("\r\n", "\n").replace("\r", "\n"))
        if sentence.strip()
    ]


def _looks_declarative(sentence: str) -> bool:
    lowered = sentence.lower().strip()
    if sentence.endswith("?"):
        return False
    first = lowered.split(maxsplit=1)[0] if lowered else ""
    if first in _COMMAND_STARTERS:
        return False
    if len(lowered.split()) < 4:
        return False
    return True


def _claim_type_for_source(source_type: str) -> BeliefClaimType:
    if source_type == "user_message":
        return "user_statement"
    if source_type == "system":
        return "system_statement"
    if source_type in {"evidence", "evidence_chunk"}:
        return "observation"
    return "generic"


def _confidence_for_source(source_type: str) -> float:
    return {
        "evidence": 0.70,
        "evidence_chunk": 0.70,
        "user_message": 0.50,
        "reasoning": 0.45,
        "system": 0.60,
    }.get(source_type, 0.50)
