"""Deterministic retrieval scoring."""

import math
import re
from datetime import UTC, datetime

from aion_brain.contracts.retrieval import RetrievalSource, RetrievedContextItem

SOURCE_WEIGHTS: dict[RetrievalSource, float] = {
    "semantic_memory": 0.90,
    "working_memory": 0.88,
    "lexical_memory": 0.85,
    "graph_memory": 0.80,
    "evidence_vault": 0.78,
    "skill_registry": 0.75,
    "capability_registry": 0.70,
    "entity_registry": 0.70,
    "concept_registry": 0.69,
    "belief_state": 0.68,
    "situation_model": 0.67,
    "temporal_state": 0.66,
    "decision_journal": 0.63,
    "recent_trace": 0.60,
    "learning_signal": 0.55,
    "policy_constraint": 0.50,
}


def score_candidate(
    *,
    source: RetrievalSource,
    base_relevance: float,
    confidence: float,
    lexical_overlap: float,
    recency_score: float,
) -> float:
    """Score a retrieval candidate using deterministic normalized features."""
    source_weight = SOURCE_WEIGHTS[source]
    score = (
        0.40 * _clamp(base_relevance)
        + 0.25 * _clamp(confidence)
        + 0.20 * _clamp(lexical_overlap)
        + 0.10 * _clamp(recency_score)
        + 0.05 * source_weight
    )
    return _clamp(score)


def rank_items(query: str, items: list[RetrievedContextItem]) -> list[RetrievedContextItem]:
    """Return items with recalculated deterministic scores in stable rank order."""
    scored = [
        item.model_copy(
            update={
                "score": score_candidate(
                    source=item.source,
                    base_relevance=_metadata_float(item, "base_relevance", item.score),
                    confidence=item.confidence,
                    lexical_overlap=lexical_overlap(query, item.content),
                    recency_score=recency_score(item),
                )
            }
        )
        for item in items
    ]
    return sorted(scored, key=lambda item: (-item.score, item.source, item.source_id))


def lexical_overlap(query: str, content: str) -> float:
    """Return exact query-token overlap normalized to 0..1."""
    query_tokens = set(_tokens(query))
    if not query_tokens:
        return 0.0
    return _clamp(len(query_tokens.intersection(set(_tokens(content)))) / len(query_tokens))


def recency_score(item: RetrievedContextItem) -> float:
    """Return a deterministic recency score from item metadata."""
    explicit = item.metadata.get("recency_score")
    if isinstance(explicit, int | float):
        return _clamp(float(explicit))
    timestamp = item.metadata.get("observed_at") or item.metadata.get("created_at")
    if isinstance(timestamp, str):
        try:
            observed_at = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        except ValueError:
            return 0.5
        age_days = max(0.0, (datetime.now(UTC) - observed_at).total_seconds() / 86400)
        return _clamp(math.exp(-age_days / 30.0))
    return 0.5


def content_hash_key(content: str) -> str:
    """Return normalized content for deterministic deduplication."""
    return " ".join(_tokens(content))


def _metadata_float(
    item: RetrievedContextItem,
    key: str,
    default: float,
) -> float:
    value = item.metadata.get(key)
    if isinstance(value, int | float):
        return float(value)
    return default


def _tokens(value: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", value.lower())


def _clamp(value: float) -> float:
    if value < 0.0:
        return 0.0
    if value > 1.0:
        return 1.0
    return value
