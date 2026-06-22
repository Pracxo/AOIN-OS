"""Deterministic evidence search."""

import re
from datetime import UTC, datetime

from aion_brain.contracts.evidence import (
    EvidenceChunk,
    EvidenceRecord,
    EvidenceSearchResult,
)

TOKEN_PATTERN = re.compile(r"[a-z0-9]+")


def search_evidence_records(
    *,
    query: str,
    evidence_records: list[EvidenceRecord],
    chunks_by_evidence_id: dict[str, list[EvidenceChunk]],
    limit: int,
    min_score: float | None = None,
) -> list[EvidenceSearchResult]:
    """Search evidence and chunks using deterministic lexical ranking."""
    query_terms = _tokens(query)
    results: list[EvidenceSearchResult] = []
    for evidence in evidence_records:
        stored_chunks = chunks_by_evidence_id.get(evidence.evidence_id)
        chunks: list[EvidenceChunk | None] = list(stored_chunks) if stored_chunks else [None]
        for chunk in chunks:
            searchable = " ".join(
                part
                for part in (
                    evidence.title,
                    evidence.summary,
                    chunk.text if chunk is not None else "",
                )
                if part
            )
            matched_terms = sorted(query_terms.intersection(_tokens(searchable)))
            if not matched_terms:
                continue
            score = _score(
                query_terms=query_terms,
                matched_terms=set(matched_terms),
                evidence=evidence,
                chunk=chunk,
            )
            if min_score is not None and score < min_score:
                continue
            results.append(
                EvidenceSearchResult(
                    evidence=evidence,
                    chunk=chunk,
                    score=score,
                    matched_terms=matched_terms,
                    metadata={"content_hash": evidence.content_hash},
                )
            )
    return sorted(
        results,
        key=lambda item: (
            -item.score,
            item.evidence.evidence_id,
            item.chunk.chunk_index if item.chunk is not None else -1,
        ),
    )[:limit]


def lexical_overlap_score(query: str, text: str) -> float:
    """Return bounded lexical token overlap."""
    query_terms = _tokens(query)
    if not query_terms:
        return 0.0
    return len(query_terms.intersection(_tokens(text))) / len(query_terms)


def _score(
    *,
    query_terms: set[str],
    matched_terms: set[str],
    evidence: EvidenceRecord,
    chunk: EvidenceChunk | None,
) -> float:
    overlap = len(matched_terms) / max(1, len(query_terms))
    title_overlap = len(query_terms.intersection(_tokens(evidence.title))) / max(
        1,
        len(query_terms),
    )
    summary_overlap = len(query_terms.intersection(_tokens(evidence.summary))) / max(
        1,
        len(query_terms),
    )
    chunk_bonus = 0.1 if chunk is not None else 0.0
    recency = _recency_score(evidence.created_at)
    score = (
        overlap * 0.45
        + title_overlap * 0.15
        + summary_overlap * 0.15
        + evidence.confidence * 0.15
        + recency * 0.10
        + chunk_bonus
    )
    return max(0.0, min(1.0, score))


def _recency_score(created_at: datetime | None) -> float:
    if created_at is None:
        return 0.5
    age_days = max(0.0, (datetime.now(UTC) - created_at).total_seconds() / 86400)
    if age_days <= 1:
        return 1.0
    if age_days >= 365:
        return 0.2
    return max(0.2, 1.0 - (age_days / 365))


def _tokens(value: str) -> set[str]:
    return set(TOKEN_PATTERN.findall(value.lower()))
