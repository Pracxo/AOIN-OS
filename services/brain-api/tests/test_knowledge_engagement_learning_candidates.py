from __future__ import annotations

from knowledge_verified_memory_test_helpers import sample_signal

from aion_brain.contracts.knowledge_verified_memory import (
    EngagementLearningCandidateKind,
    EngagementSignalKind,
)
from aion_brain.knowledge_intelligence.engagement_learning_candidates import (
    build_engagement_learning_candidates,
)
from aion_brain.knowledge_intelligence.engagement_signal_policy import (
    build_engagement_signal_batch,
)


def test_engagement_learning_maps_every_authorized_candidate_kind() -> None:
    signals = (
        sample_signal(signal_id="signal-001", signal_kind=EngagementSignalKind.QUERY_REPEATED),
        sample_signal(
            signal_id="signal-002",
            signal_kind=EngagementSignalKind.CLARIFICATION_REQUESTED,
        ),
        sample_signal(signal_id="signal-003", signal_kind=EngagementSignalKind.RETRIEVAL_FAILED),
        sample_signal(
            signal_id="signal-004",
            signal_kind=EngagementSignalKind.RETRIEVAL_SUCCEEDED,
        ),
        sample_signal(
            signal_id="signal-005",
            signal_kind=EngagementSignalKind.CORRECTION_SUBMITTED,
            outcome="domain-routing-mismatch",
        ),
        sample_signal(
            signal_id="signal-006",
            signal_kind=EngagementSignalKind.CORRECTION_SUBMITTED,
            outcome="verification-rule-failure",
        ),
        sample_signal(
            signal_id="signal-007",
            signal_kind=EngagementSignalKind.CORRECTION_SUBMITTED,
            outcome="missing-explicit-tool-capability",
        ),
        sample_signal(signal_id="signal-008", signal_kind=EngagementSignalKind.RESPONSE_REJECTED),
        sample_signal(
            signal_id="signal-009",
            signal_kind=EngagementSignalKind.TASK_OUTCOME_REPORTED,
            metadata_codes=("stable-preference",),
        ),
    )
    batch = build_engagement_signal_batch(batch_id="signals-001", signals=signals)
    learning = build_engagement_learning_candidates(
        batch_id="learning-001",
        signal_batch=batch,
    )
    assert {candidate.candidate_kind for candidate in learning.candidates} == set(
        EngagementLearningCandidateKind
    )
    assert all(candidate.operator_review_required for candidate in learning.candidates)
