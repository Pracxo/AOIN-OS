"""Deterministic belief confidence scoring."""

from __future__ import annotations

from aion_brain.contracts.beliefs import BeliefContradiction, BeliefSupport


def score_belief_confidence(
    base_confidence: float,
    supports: list[BeliefSupport],
    contradictions: list[BeliefContradiction],
    evidence_refs: list[str],
    memory_refs: list[str],
    source_type: str,
    age_days: float | None = None,
) -> float:
    """Score a belief without model calls or domain-specific weights."""
    score = _clamp(base_confidence)
    evidence_strength = sum(
        support.strength * support.confidence
        for support in supports
        if support.support_type == "evidence"
        or support.source_type in {"evidence", "evidence_chunk"}
    )
    memory_strength = sum(
        support.strength * support.confidence
        for support in supports
        if support.support_type == "memory" or support.source_type == "memory"
    )
    audit_strength = sum(
        support.strength * support.confidence
        for support in supports
        if support.support_type in {"audit", "provenance"}
    )
    independent_sources = {
        f"{support.source_type}:{support.source_id}"
        for support in supports
        if support.deleted_at is None and support.relation_type != "contradicts"
    }
    open_contradictions = [
        contradiction for contradiction in contradictions if contradiction.status == "open"
    ]
    score += min(0.25, 0.08 * len(evidence_refs) + 0.08 * evidence_strength)
    score += min(0.15, 0.04 * len(independent_sources))
    score += min(0.05, 0.03 * len(memory_refs) + 0.04 * memory_strength)
    score += min(0.10, 0.08 * audit_strength)
    if source_type in {"evidence", "evidence_chunk"} and evidence_refs:
        score += 0.03
    score -= min(0.45, sum(_contradiction_penalty(item) for item in open_contradictions))
    if age_days is not None and age_days > 0:
        score -= min(0.20, age_days / 900.0)
    return _clamp(score)


def _contradiction_penalty(contradiction: BeliefContradiction) -> float:
    return {
        "low": 0.08,
        "medium": 0.18,
        "high": 0.32,
        "critical": 0.45,
    }.get(contradiction.severity, 0.18)


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))
