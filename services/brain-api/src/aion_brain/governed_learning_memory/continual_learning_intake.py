"""Non-factual engagement intake for AION-228."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from aion_brain.contracts.governed_continual_learning import (
    ContinualLearningEngagementIntake,
    ContinualLearningError,
    build_record,
    continual_fingerprint,
    utc_now,
)


def _record_fingerprint(record: Any) -> str:
    if hasattr(record, "model_dump"):
        payload = record.model_dump(mode="json")
    elif hasattr(record, "__dict__"):
        payload = vars(record)
    else:
        payload = record
    return continual_fingerprint({"engagement_record": payload})


def _assert_non_factual(record: Any) -> None:
    payload = record.model_dump(mode="json") if hasattr(record, "model_dump") else record
    text = str(payload).lower()
    if any(
        marker in text
        for marker in (
            "factual_truth",
            "confidence_effect': true",
            "knowledge_effect': true",
            "source_independence_effect': true",
            "belief_effect': true",
        )
    ):
        raise ContinualLearningError("engagement intake must remain non-factual")


def build_continual_learning_engagement_intake(
    *,
    session_id: str,
    cycle_id: str,
    selected_candidate_id: str,
    selected_candidate_kind: str,
    signal_records: Iterable[Any],
    candidate_records: Iterable[Any],
    intake_role: str,
) -> ContinualLearningEngagementIntake:
    """Build a redacted intake binding from non-factual engagement records."""

    signals = tuple(signal_records)
    candidates = tuple(candidate_records)
    for item in (*signals, *candidates):
        _assert_non_factual(item)
    return build_record(
        ContinualLearningEngagementIntake,
        {
            "schema_version": "aion-glm-continual-learning-engagement-intake/v1",
            "intake_id": f"{cycle_id}-intake",
            "session_id": session_id,
            "cycle_id": cycle_id,
            "selected_candidate_id": selected_candidate_id,
            "selected_candidate_kind": selected_candidate_kind,
            "signal_fingerprints": tuple(_record_fingerprint(item) for item in signals),
            "candidate_fingerprints": tuple(_record_fingerprint(item) for item in candidates),
            "intake_role": intake_role,
            "created_at": utc_now(),
        },
        "intake_fingerprint",
    )
