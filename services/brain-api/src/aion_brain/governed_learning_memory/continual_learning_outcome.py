"""Outcome and exact-query helpers for AION-228."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from aion_brain.contracts.governed_continual_learning import (
    ContinualLearningCycleOutcome,
    ContinualLearningQuery,
    ContinualLearningQueryResult,
    ContinualLearningSessionResult,
    build_record,
    continual_fingerprint,
)


def build_cycle_outcome(**payload: Any) -> ContinualLearningCycleOutcome:
    """Build a fingerprinted cycle outcome."""

    return build_record(ContinualLearningCycleOutcome, payload, "outcome_fingerprint")


def build_session_result(**payload: Any) -> ContinualLearningSessionResult:
    """Build a fingerprinted session result."""

    return build_record(ContinualLearningSessionResult, payload, "result_fingerprint")


def build_exact_query(
    *,
    query_id: str,
    filters: dict[str, str],
    limit: int = 1000,
) -> ContinualLearningQuery:
    """Build an exact read-only query."""

    return build_record(
        ContinualLearningQuery,
        {
            "schema_version": "aion-glm-continual-learning-query/v1",
            "query_id": query_id,
            "filters": dict(sorted(filters.items())),
            "limit": limit,
        },
        "query_fingerprint",
    )


def run_exact_query(
    query: ContinualLearningQuery,
    records: Iterable[Any],
    *,
    id_field: str,
    fingerprint_field: str,
) -> ContinualLearningQueryResult:
    """Run deterministic exact matching over in-memory records."""

    matches: list[Any] = []
    for record in records:
        payload = record.model_dump(mode="json") if hasattr(record, "model_dump") else dict(record)
        if all(str(payload.get(key)) == expected for key, expected in query.filters.items()):
            matches.append(record)
    matches = sorted(matches, key=lambda item: getattr(item, id_field))
    limited = matches[: query.limit]
    return build_record(
        ContinualLearningQueryResult,
        {
            "schema_version": "aion-glm-continual-learning-query-result/v1",
            "query_id": query.query_id,
            "result_ids": tuple(getattr(item, id_field) for item in limited),
            "result_fingerprints": tuple(getattr(item, fingerprint_field) for item in limited),
            "result_count": len(limited),
        },
        "result_fingerprint",
    )


def synthetic_query_fingerprint(query_id: str, payload: object) -> str:
    """Return a deterministic exact-query evidence fingerprint."""

    return continual_fingerprint({"query_id": query_id, "payload": payload})
