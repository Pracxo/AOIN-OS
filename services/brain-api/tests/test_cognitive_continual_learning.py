"""AION-196 governed continual-learning contract and service tests."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from aion_brain.continual_learning import (
    LEARNING_LEVELS,
    REQUIRED_PIPELINE,
    CandidateLearningService,
    CandidatePromotionPolicy,
    CatastrophicForgettingEvaluator,
    ExperienceReplayService,
    LearningBenchmarkEvaluator,
    LearningRollbackService,
)
from aion_brain.contracts.continual_learning import (
    ContinualLearningObservation,
    LearningCandidate,
    LearningEpisode,
    LearningEvaluation,
    PromotionRequest,
    ReplaySample,
)

NOW = datetime(2026, 7, 22, 4, 15, tzinfo=UTC)


def observation(
    observation_id: str,
    summary: str,
    *,
    confidence: float = 0.9,
    step: str | None = None,
) -> ContinualLearningObservation:
    metadata: dict[str, object] = {}
    if step is not None:
        metadata["step"] = step
    return ContinualLearningObservation(
        observation_id=observation_id,
        source="aion-196-fixture",
        summary=summary,
        signal_tags=("policy:governed-learning",),
        evidence_refs=(f"aion://aion-196/observation/{observation_id}",),
        confidence=confidence,
        observed_at=NOW,
        metadata=metadata,
    )


def episode(
    episode_id: str,
    summary: str,
    *,
    protected_holdout: bool = False,
    confidence: float = 0.9,
    minutes: int = 0,
    step: str | None = None,
) -> LearningEpisode:
    return LearningEpisode(
        episode_id=episode_id,
        observations=(
            observation(
                f"observation-{episode_id}",
                summary,
                confidence=confidence,
                step=step,
            ),
        ),
        outcome_label="success" if confidence >= 0.8 else "review",
        baseline_ref="baseline://aion-196/immutable-baseline",
        policy_ref="policy://aion-196/promotion-policy",
        evidence_refs=(f"aion://aion-196/episode/{episode_id}",),
        protected_holdout=protected_holdout,
        allowed_for_replay=not protected_holdout,
        occurred_at=NOW + timedelta(minutes=minutes),
    )


def learning_fixtures() -> tuple[LearningEpisode, ...]:
    return (
        episode(
            "episode-memory",
            "memory evidence retained for replay",
            confidence=0.95,
            minutes=1,
            step="review replayed memory evidence",
        ),
        episode(
            "episode-policy",
            "retrieval and planning policy evidence",
            confidence=0.9,
            minutes=2,
            step="compare policy candidate against baseline",
        ),
        episode(
            "episode-holdout",
            "protected holdout benchmark evidence",
            protected_holdout=True,
            confidence=0.92,
            minutes=3,
            step="holdout benchmark remains unseen by replay",
        ),
    )


def test_contracts_are_immutable_fingerprinted_and_secret_safe() -> None:
    first = observation("observation-contract", "contract evidence")
    second = observation("observation-contract", "contract evidence")

    assert first.fingerprint == second.fingerprint
    with pytest.raises(ValidationError):
        first.observation_id = "changed"  # type: ignore[misc]
    with pytest.raises(TypeError):
        first.metadata["step"] = "changed"
    with pytest.raises(ValidationError):
        observation("observation-secret", "safe", step="sk-test-secret")


def test_replay_excludes_protected_holdout_and_is_deterministic() -> None:
    replay = ExperienceReplayService()
    first = replay.select(learning_fixtures(), sample_id="aion-196-replay", max_episodes=2)
    second = replay.select(
        reversed(learning_fixtures()),
        sample_id="aion-196-replay",
        max_episodes=2,
    )

    assert first.deterministic_replay_hash == second.deterministic_replay_hash
    assert first.episode_ids == ("episode-memory", "episode-policy")
    assert first.excluded_holdout_episode_ids == ("episode-holdout",)
    assert first.runtime_effect is False
    assert first.network_calls == 0

    with pytest.raises(ValidationError):
        ReplaySample(
            sample_id="bad-replay",
            episode_ids=("episode-holdout",),
            excluded_holdout_episode_ids=("episode-holdout",),
            baseline_ref="baseline://aion-196/immutable-baseline",
            policy_ref="policy://aion-196/promotion-policy",
            max_episodes=1,
            generated_at=NOW,
        )


def test_candidate_learning_covers_all_authorized_levels_and_remains_isolated() -> None:
    fixtures = learning_fixtures()
    replay = ExperienceReplayService().select(
        fixtures,
        sample_id="aion-196-candidate-replay",
        max_episodes=2,
    )
    candidates = CandidateLearningService().learn(fixtures, replay)

    assert REQUIRED_PIPELINE == (
        "immutable baseline",
        "protected holdout split",
        "deterministic replay",
        "isolated candidate learning",
        "catastrophic forgetting evaluation",
        "protected holdout benchmark",
        "approval-bound promotion review",
        "rollback plan",
    )
    assert set(LEARNING_LEVELS) == {candidate.candidate_type for candidate in candidates}
    assert len(candidates) == 6
    assert {candidate.version for candidate in candidates} == {1}
    assert all(candidate.operator_review_required for candidate in candidates)
    assert all(candidate.candidate_isolated for candidate in candidates)
    assert all(not candidate.promotion_allowed for candidate in candidates)
    assert all("episode-holdout" not in candidate.source_episode_ids for candidate in candidates)

    with pytest.raises(ValidationError):
        LearningCandidate(
            candidate_id="bad-auto-promotion",
            candidate_type="memory",
            version=1,
            baseline_ref=replay.baseline_ref,
            replay_sample_id=replay.sample_id,
            source_episode_ids=("episode-memory",),
            summary="bad automatic promotion",
            confidence=0.9,
            evidence_refs=("aion://aion-196/candidate/bad",),
            promotion_allowed=True,
            generated_at=NOW,
        )


def test_forgetting_benchmark_promotion_and_rollback_are_governed() -> None:
    fixtures = learning_fixtures()
    replay = ExperienceReplayService().select(
        fixtures,
        sample_id="aion-196-evaluation-replay",
        max_episodes=2,
    )
    holdout = tuple(episode for episode in fixtures if episode.protected_holdout)
    candidates = CandidateLearningService().learn(fixtures, replay)
    risk_evaluator = CatastrophicForgettingEvaluator()
    benchmark = LearningBenchmarkEvaluator()
    promotion_policy = CandidatePromotionPolicy()
    rollback = LearningRollbackService()

    for candidate in candidates:
        risk = risk_evaluator.evaluate(candidate, replay_sample=replay, holdout_episodes=holdout)
        evaluation = benchmark.evaluate(
            candidate,
            replay_sample=replay,
            forgetting_risk=risk,
        )
        request = promotion_policy.review(
            candidate,
            evaluation,
            requested_by="operator",
        )
        rollback_plan = rollback.plan(candidate)

        assert risk.catastrophic_forgetting_detected is False
        assert evaluation.protected_holdout_score == 1.0
        assert evaluation.baseline_regression_rate == 0.0
        assert evaluation.approved_for_promotion is False
        assert request.status == "operator_review_required"
        assert request.promotion_performed is False
        assert rollback_plan.rollback_available is True
        assert rollback_plan.source_restore_required is False
        assert rollback_plan.model_weight_restore_required is False

    first = candidates[0]
    first_risk = risk_evaluator.evaluate(first, replay_sample=replay, holdout_episodes=holdout)
    first_evaluation = benchmark.evaluate(
        first,
        replay_sample=replay,
        forgetting_risk=first_risk,
    )
    approved = promotion_policy.review(
        first,
        first_evaluation,
        requested_by="operator",
        approved_by="review-board",
        approval_ref="operator-approved://aion-196/review-board",
    )
    assert approved.status == "approved_by_external_governance"
    assert approved.promotion_performed is False

    with pytest.raises(ValidationError):
        promotion_policy.review(
            first,
            first_evaluation,
            requested_by="operator",
            approved_by="operator",
            approval_ref="operator-approved://aion-196/self-approval",
        )
    with pytest.raises(ValidationError):
        PromotionRequest(
            request_id="bad-automatic",
            candidate_id=first.candidate_id,
            candidate_version=first.version,
            evaluation_id=first_evaluation.evaluation_id,
            requested_by="operator",
            automatic_promotion=True,
            created_at=NOW,
        )
    with pytest.raises(ValidationError):
        LearningEvaluation(
            evaluation_id="bad-approved-evaluation",
            candidate_id=first.candidate_id,
            candidate_version=first.version,
            replay_sample_id=replay.sample_id,
            forgetting_risk=first_risk,
            protected_holdout_score=1.0,
            baseline_regression_rate=0.0,
            approved_for_promotion=True,
            generated_at=NOW,
        )
