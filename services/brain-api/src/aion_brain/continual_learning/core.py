"""Deterministic local continual-learning services."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import UTC, datetime

from aion_brain.contracts.continual_learning import (
    ForgettingRisk,
    LearningCandidate,
    LearningEpisode,
    LearningEvaluation,
    LearningRollbackPlan,
    PlanningPolicyCandidate,
    ProceduralSkillCandidate,
    PromotionRequest,
    ReplaySample,
    RetrievalPolicyCandidate,
    StrategyCandidate,
    WorldModelAdapterCandidate,
)

GENERATED_AT = datetime(1970, 1, 1, tzinfo=UTC)

LEARNING_LEVELS = (
    "memory",
    "retrieval_policy",
    "planning_policy",
    "procedural_skill",
    "world_model_adapter",
    "strategy",
)

REQUIRED_PIPELINE = (
    "immutable baseline",
    "protected holdout split",
    "deterministic replay",
    "isolated candidate learning",
    "catastrophic forgetting evaluation",
    "protected holdout benchmark",
    "approval-bound promotion review",
    "rollback plan",
)


class ExperienceReplayService:
    """Create deterministic replay samples while excluding protected holdout."""

    def select(
        self,
        episodes: Iterable[LearningEpisode],
        *,
        sample_id: str,
        max_episodes: int,
    ) -> ReplaySample:
        if max_episodes < 1:
            raise ValueError("max_episodes must be positive")
        by_episode: dict[str, LearningEpisode] = {}
        holdout_ids: set[str] = set()
        for episode in episodes:
            if episode.protected_holdout or not episode.allowed_for_replay:
                holdout_ids.add(episode.episode_id)
                continue
            existing = by_episode.get(episode.episode_id)
            if existing is None or self._rank_key(episode) < self._rank_key(existing):
                by_episode[episode.episode_id] = episode
        ranked = tuple(sorted(by_episode.values(), key=self._rank_key))
        selected = ranked[:max_episodes]
        if not selected:
            raise ValueError("replay requires at least one non-holdout episode")
        return ReplaySample(
            sample_id=sample_id,
            episode_ids=tuple(episode.episode_id for episode in selected),
            excluded_holdout_episode_ids=tuple(sorted(holdout_ids)),
            baseline_ref=selected[0].baseline_ref,
            policy_ref=selected[0].policy_ref,
            max_episodes=max_episodes,
            generated_at=GENERATED_AT,
        )

    def _rank_key(self, episode: LearningEpisode) -> tuple[str, float, str]:
        confidence = _average(
            observation.confidence for observation in episode.observations
        )
        return (episode.occurred_at.isoformat(), -confidence, episode.episode_id)


class CandidateLearningService:
    """Generate isolated review candidates for each authorized learning level."""

    def learn(
        self,
        episodes: Iterable[LearningEpisode],
        replay_sample: ReplaySample,
    ) -> tuple[
        LearningCandidate
        | RetrievalPolicyCandidate
        | PlanningPolicyCandidate
        | ProceduralSkillCandidate
        | WorldModelAdapterCandidate
        | StrategyCandidate,
        ...,
    ]:
        by_id = {episode.episode_id: episode for episode in episodes}
        selected = tuple(by_id[episode_id] for episode_id in replay_sample.episode_ids)
        source_episode_ids = tuple(episode.episode_id for episode in selected)
        evidence_refs = _combined_refs(
            (
                replay_sample.deterministic_replay_hash or "",
                *tuple(episode.evidence_refs for episode in selected),
                *tuple(
                    observation.evidence_refs
                    for episode in selected
                    for observation in episode.observations
                ),
            )
        )
        confidence = _average(
            observation.confidence for episode in selected for observation in episode.observations
        )
        return (
            LearningCandidate(
                candidate_id="candidate-memory-v1",
                candidate_type="memory",
                version=1,
                baseline_ref=replay_sample.baseline_ref,
                replay_sample_id=replay_sample.sample_id,
                source_episode_ids=source_episode_ids,
                summary="memory candidate preserves replayed evidence for review",
                confidence=confidence,
                evidence_refs=evidence_refs,
                generated_at=GENERATED_AT,
            ),
            RetrievalPolicyCandidate(
                candidate_id="candidate-retrieval-policy-v1",
                version=1,
                baseline_ref=replay_sample.baseline_ref,
                replay_sample_id=replay_sample.sample_id,
                source_episode_ids=source_episode_ids,
                summary="retrieval policy candidate ranks approved evidence by replay confidence",
                confidence=confidence,
                evidence_refs=evidence_refs,
                query_policy="prefer explicit evidence refs from replayed successful episodes",
                ranking_rule="rank by observation confidence then episode time",
                allowed_source_refs=tuple(sorted(evidence_refs)),
                generated_at=GENERATED_AT,
            ),
            PlanningPolicyCandidate(
                candidate_id="candidate-planning-policy-v1",
                version=1,
                baseline_ref=replay_sample.baseline_ref,
                replay_sample_id=replay_sample.sample_id,
                source_episode_ids=source_episode_ids,
                summary="planning policy candidate preserves budget and rollback constraints",
                confidence=confidence,
                evidence_refs=evidence_refs,
                planning_rule="prefer reversible steps until protected evidence is reviewed",
                budget_policy="keep replay-derived plan cost within the immutable baseline budget",
                replanning_trigger="replan when holdout benchmark confidence falls below threshold",
                generated_at=GENERATED_AT,
            ),
            ProceduralSkillCandidate(
                candidate_id="candidate-procedural-skill-v1",
                version=1,
                baseline_ref=replay_sample.baseline_ref,
                replay_sample_id=replay_sample.sample_id,
                source_episode_ids=source_episode_ids,
                summary="procedural skill candidate captures replayed successful review steps",
                confidence=confidence,
                evidence_refs=evidence_refs,
                skill_name="governed replay review",
                steps=tuple(_step_text(episode) for episode in selected),
                preconditions=("operator review required", "rollback plan available"),
                generated_at=GENERATED_AT,
            ),
            WorldModelAdapterCandidate(
                candidate_id="candidate-world-model-adapter-v1",
                version=1,
                baseline_ref=replay_sample.baseline_ref,
                replay_sample_id=replay_sample.sample_id,
                source_episode_ids=source_episode_ids,
                summary="world-model adapter candidate records replay transition expectations",
                confidence=confidence,
                evidence_refs=evidence_refs,
                adapter_name="local replay transition adapter",
                predicted_transition=(
                    "successful review episodes reduce uncertainty without mutation"
                ),
                uncertainty_delta=round(min(1.0, max(0.0, confidence * 0.2)), 12),
                generated_at=GENERATED_AT,
            ),
            StrategyCandidate(
                candidate_id="candidate-strategy-v1",
                version=1,
                baseline_ref=replay_sample.baseline_ref,
                replay_sample_id=replay_sample.sample_id,
                source_episode_ids=source_episode_ids,
                summary="strategy candidate selects approval-bound learning only after benchmarks",
                confidence=confidence,
                evidence_refs=evidence_refs,
                strategy_name="approval-bound replay candidate strategy",
                selection_rule="select candidates with no forgetting risk and rollback available",
                expected_goal_progress=round(min(1.0, confidence), 12),
                generated_at=GENERATED_AT,
            ),
        )


class CatastrophicForgettingEvaluator:
    """Evaluate holdout and baseline risk without mutating candidates."""

    def evaluate(
        self,
        candidate: LearningCandidate,
        *,
        replay_sample: ReplaySample,
        holdout_episodes: Iterable[LearningEpisode],
    ) -> ForgettingRisk:
        holdout_ids = {episode.episode_id for episode in holdout_episodes}
        leaked_holdout = bool(set(candidate.source_episode_ids) & holdout_ids)
        protected_score = 0.0 if leaked_holdout else 1.0
        regression_rate = 1.0 if leaked_holdout else 0.0
        return ForgettingRisk(
            risk_id=f"forgetting-{candidate.candidate_id}",
            candidate_id=candidate.candidate_id,
            baseline_ref=candidate.baseline_ref,
            protected_holdout_score=protected_score,
            baseline_regression_rate=regression_rate,
            contradiction_loss_rate=0.0,
            catastrophic_forgetting_detected=leaked_holdout,
            risk_level="critical" if leaked_holdout else "low",
            evidence_refs=(
                replay_sample.deterministic_replay_hash or "",
                f"holdout://{replay_sample.sample_id}/protected",
            ),
            generated_at=GENERATED_AT,
        )


class LearningBenchmarkEvaluator:
    """Create protected-holdout benchmark evidence for an isolated candidate."""

    def evaluate(
        self,
        candidate: LearningCandidate,
        *,
        replay_sample: ReplaySample,
        forgetting_risk: ForgettingRisk,
    ) -> LearningEvaluation:
        return LearningEvaluation(
            evaluation_id=f"evaluation-{candidate.candidate_id}",
            candidate_id=candidate.candidate_id,
            candidate_version=candidate.version,
            replay_sample_id=replay_sample.sample_id,
            forgetting_risk=forgetting_risk,
            protected_holdout_score=forgetting_risk.protected_holdout_score,
            baseline_regression_rate=forgetting_risk.baseline_regression_rate,
            deterministic_replay=True,
            candidate_isolation_verified=candidate.candidate_isolated,
            rollback_available=True,
            promotion_requires_approval=True,
            approved_for_promotion=False,
            evidence_refs=_combined_refs(
                (
                    candidate.evidence_refs,
                    forgetting_risk.evidence_refs,
                    replay_sample.deterministic_replay_hash or "",
                )
            ),
            generated_at=GENERATED_AT,
        )


class CandidatePromotionPolicy:
    """Create promotion review records without self-approval or automatic promotion."""

    def review(
        self,
        candidate: LearningCandidate,
        evaluation: LearningEvaluation,
        *,
        requested_by: str,
        approved_by: str | None = None,
        approval_ref: str | None = None,
    ) -> PromotionRequest:
        if approved_by is not None and approval_ref is not None:
            return PromotionRequest(
                request_id=f"promotion-{candidate.candidate_id}",
                candidate_id=candidate.candidate_id,
                candidate_version=candidate.version,
                evaluation_id=evaluation.evaluation_id,
                requested_by=requested_by,
                status="approved_by_external_governance",
                approved_by=approved_by,
                approval_ref=approval_ref,
                promotion_performed=False,
                created_at=GENERATED_AT,
            )
        return PromotionRequest(
            request_id=f"promotion-{candidate.candidate_id}",
            candidate_id=candidate.candidate_id,
            candidate_version=candidate.version,
            evaluation_id=evaluation.evaluation_id,
            requested_by=requested_by,
            status="operator_review_required",
            approved_by=approved_by,
            approval_ref=approval_ref,
            promotion_performed=False,
            created_at=GENERATED_AT,
        )


class LearningRollbackService:
    """Create rollback plans that restore the immutable baseline."""

    def plan(self, candidate: LearningCandidate) -> LearningRollbackPlan:
        return LearningRollbackPlan(
            plan_id=f"rollback-{candidate.candidate_id}",
            candidate_id=candidate.candidate_id,
            candidate_version=candidate.version,
            baseline_ref=candidate.baseline_ref,
            rollback_steps=(
                f"retain immutable baseline {candidate.baseline_ref}",
                f"discard isolated candidate {candidate.candidate_id} if review rejects it",
                "keep protected holdout unchanged",
            ),
            rollback_available=True,
            source_restore_required=False,
            model_weight_restore_required=False,
            created_at=GENERATED_AT,
        )


def _step_text(episode: LearningEpisode) -> str:
    for observation in episode.observations:
        step = observation.metadata.get("step")
        if isinstance(step, str) and step.strip():
            return step.strip()
    return episode.outcome_label


def _combined_refs(items: Iterable[Iterable[str] | str]) -> tuple[str, ...]:
    refs: set[str] = set()
    for item in items:
        if isinstance(item, str):
            if item:
                refs.add(item)
            continue
        refs.update(ref for ref in item if ref)
    return tuple(sorted(refs))


def _average(values: Iterable[float]) -> float:
    numbers = tuple(values)
    if not numbers:
        return 0.0
    return round(sum(numbers) / len(numbers), 12)
