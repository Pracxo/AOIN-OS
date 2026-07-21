"""AION-190 memory-consolidation contract and service tests."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from aion_brain.contracts.memory_consolidation import (
    ConsolidationCheckpoint,
    EpisodicMemoryReference,
    ReplayBatch,
    SemanticCandidate,
)
from aion_brain.memory_consolidation import (
    REQUIRED_PIPELINE,
    ConsolidationService,
    EpisodicReplayPlanner,
)

NOW = datetime(2026, 7, 21, 17, 30, tzinfo=UTC)


def episode(
    episode_id: str,
    summary: str,
    *,
    concept: str = "release gate",
    statement: str | None = None,
    tags: tuple[str, ...] = (),
    importance: float = 0.5,
    confidence: float = 0.8,
    safety_critical: bool = False,
    retention_required: bool = False,
    step: str | None = None,
    step_index: int = 0,
    outcome: str = "success",
    policy_evidence_ref: str | None = None,
) -> EpisodicMemoryReference:
    metadata: dict[str, object] = {
        "semantic_statement": statement or summary,
        "outcome": outcome,
    }
    if step is not None:
        metadata["step"] = step
        metadata["step_index"] = step_index
    if policy_evidence_ref is not None:
        metadata["policy_evidence_ref"] = policy_evidence_ref
    return EpisodicMemoryReference(
        episode_id=episode_id,
        source="aion-190-fixture",
        content_summary=summary,
        occurred_at=NOW + timedelta(minutes=step_index),
        salience_tags=(f"concept:{concept}", *tags),
        evidence_refs=(f"aion://aion-190/episode/{episode_id}",),
        importance=importance,
        confidence=confidence,
        safety_critical=safety_critical,
        retention_required=retention_required,
        metadata=metadata,
    )


def replay_fixtures() -> tuple[EpisodicMemoryReference, ...]:
    return (
        episode(
            "episode-safe-retention",
            "critical release hold retained",
            statement="release gate remains disabled until review",
            importance=1.0,
            confidence=0.96,
            safety_critical=True,
            retention_required=True,
            tags=("procedure:release-check",),
            step="verify runtime hold",
            step_index=1,
        ),
        episode(
            "episode-green-release",
            "green release gate evidence",
            statement="release gate passes when checks are green",
            importance=0.8,
            confidence=0.9,
            tags=("procedure:release-check",),
            step="collect green check evidence",
            step_index=2,
        ),
        episode(
            "episode-pending-release",
            "pending release gate evidence",
            statement="release gate waits when checks are pending",
            importance=0.7,
            confidence=0.82,
            tags=("procedure:release-check",),
            step="hold merge while checks are pending",
            step_index=3,
            outcome="failure",
        ),
        episode(
            "episode-duplicate-primary",
            "duplicate replay marker",
            concept="duplicate replay",
            statement="duplicate replay marker can be compacted",
            importance=0.6,
            confidence=0.8,
        ),
        episode(
            "episode-duplicate-secondary",
            "duplicate replay marker",
            concept="duplicate replay",
            statement="duplicate replay marker can be compacted",
            importance=0.4,
            confidence=0.75,
            policy_evidence_ref="aion://aion-190/policy/duplicate-retention",
        ),
    )


def test_contracts_are_immutable_safe_and_fingerprinted() -> None:
    reference = episode("episode-contract", "immutable memory reference")
    same_reference = episode("episode-contract", "immutable memory reference")

    assert reference.fingerprint == same_reference.fingerprint
    assert reference.metadata["semantic_statement"] == "immutable memory reference"
    with pytest.raises(ValidationError):
        reference.episode_id = "changed"  # type: ignore[misc]
    with pytest.raises(TypeError):
        reference.metadata["semantic_statement"] = "changed"
    with pytest.raises(ValidationError):
        episode("episode-secret", "safe summary", policy_evidence_ref="sk-test-secret")


def test_replay_batch_is_deterministic_and_duplicate_closed() -> None:
    planner = EpisodicReplayPlanner()
    first = planner.plan(replay_fixtures(), batch_id="aion-190-batch", max_items=5)
    second = planner.plan(reversed(replay_fixtures()), batch_id="aion-190-batch", max_items=5)

    assert first.replay_hash == second.replay_hash
    assert [reference.episode_id for reference in first.references][0] == "episode-safe-retention"
    assert first.runtime_effect is False
    assert first.network_calls == 0
    with pytest.raises(ValidationError):
        ReplayBatch(
            batch_id="duplicate-batch",
            references=(first.references[0], first.references[0]),
            selection_reason="duplicate rejected",
            max_items=2,
            generated_at=NOW,
        )


def test_consolidation_pipeline_generates_review_candidates_and_evidence() -> None:
    outcome = ConsolidationService().run(
        replay_fixtures(),
        batch_id="aion-190-pipeline",
        max_items=5,
        outcome_id="aion-190-outcome",
    )

    assert outcome.pipeline_stages == REQUIRED_PIPELINE
    assert len(outcome.semantic_candidates) >= 3
    assert {candidate.procedure_name for candidate in outcome.procedural_candidates} == {
        "release-check"
    }
    assert outcome.contradiction_resolutions
    assert outcome.forgetting_candidates
    assert outcome.checkpoint.operator_review_required is True
    assert outcome.checkpoint.promotion_status == "operator_review_required"
    assert outcome.checkpoint.evidence.retained_critical_memories_rate == 1.0
    assert outcome.checkpoint.evidence.contradiction_loss_rate == 0.0
    assert outcome.checkpoint.evidence.unauthorized_promotion_count == 0
    assert outcome.checkpoint.evidence.provenance_coverage == 1.0
    assert outcome.promotion_performed is False
    assert outcome.source_rewrite_performed is False
    assert outcome.hidden_mutation_performed is False
    assert outcome.deletion_performed is False


def test_promotion_and_checkpoint_approval_remain_governance_gated() -> None:
    reference = episode("episode-review", "review gate evidence")
    with pytest.raises(ValidationError):
        SemanticCandidate(
            candidate_id="semantic-approved",
            source_episode_ids=(reference.episode_id,),
            summary="review gate evidence",
            confidence=0.9,
            evidence_refs=reference.evidence_refs,
            concept_key="review gate",
            normalized_statement="review gate evidence",
            supporting_episode_ids=(reference.episode_id,),
            approved_for_promotion=True,
            generated_at=NOW,
        )

    outcome = ConsolidationService().run(
        (reference,),
        batch_id="aion-190-review",
        max_items=1,
        outcome_id="aion-190-review-outcome",
    )
    with pytest.raises(ValidationError):
        ConsolidationCheckpoint(
            checkpoint_id="checkpoint-invalid-approval",
            replay_batch=outcome.checkpoint.replay_batch,
            candidates=outcome.checkpoint.candidates,
            evidence=outcome.checkpoint.evidence,
            operator_review_required=True,
            promotion_status="approved_by_existing_governance",
            automatic_promotion_performed=True,
            created_at=NOW,
        )
