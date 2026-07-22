"""AION-199 integrated cognitive shadow-runtime tests."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from aion_brain.cognitive_architecture import (
    CognitiveStateService,
    InMemoryCognitiveStateRepository,
)
from aion_brain.cognitive_runtime import (
    CognitiveRuntimeBoundaryError,
    ControlledCognitiveShadowRuntime,
)
from aion_brain.contracts.cognitive_runtime import (
    AUTHORIZATION_ID,
    REQUIRED_CYCLE_STEPS,
    ApprovedCognitiveObservation,
    CognitiveCycleInput,
    CognitiveRuntimeBudget,
    CognitiveSessionManifest,
)
from aion_brain.contracts.cognitive_state import CognitiveStateProvenance
from aion_brain.contracts.continual_learning import (
    ContinualLearningObservation,
    LearningEpisode,
)
from aion_brain.contracts.information_acquisition import InformationNeed
from aion_brain.contracts.memory_consolidation import EpisodicMemoryReference
from aion_brain.contracts.planning import StrategicGoal, StrategyOption
from aion_brain.contracts.world_model import (
    TransitionEvidence,
    WorldActionReference,
    WorldState,
)

NOW = datetime(2026, 7, 22, 8, 30, tzinfo=UTC)


def manifest(*, max_cycles: int = 100, kill_switch: bool = False) -> CognitiveSessionManifest:
    return CognitiveSessionManifest(
        session_id="aion-199-session",
        operator_id="operator-aion-199",
        input_kind="synthetic",
        state_repository_ref="local://aion-199/shadow-state",
        budget=CognitiveRuntimeBudget(max_cycles_per_invocation=max_cycles),
        kill_switch_engaged=kill_switch,
        created_at=NOW,
    )


def world_state(state_id: str, *, readiness: str, uncertainty: float) -> WorldState:
    return WorldState(
        state_id=state_id,
        features={
            "readiness": readiness,
            "uncertainty": uncertainty,
            "review_required": True,
        },
        provenance_refs=(f"aion://aion-199/world/{state_id}",),
        observed_at=NOW,
    )


def action() -> WorldActionReference:
    return WorldActionReference(
        action_id="action-local-shadow-review",
        name="local shadow review proposal",
        parameters={"mode": "review_only"},
        reversible=True,
        irreversible_effect=False,
        evidence_refs=("aion://aion-199/action/local-shadow-review",),
        created_at=NOW,
    )


def transition_evidence() -> tuple[TransitionEvidence, ...]:
    return (
        TransitionEvidence(
            evidence_id="transition-shadow-review",
            source_state=world_state("state-before", readiness="draft", uncertainty=0.7),
            action=action(),
            outcome_state=world_state("state-after", readiness="reviewable", uncertainty=0.35),
            evidence_refs=("aion://aion-199/transition/shadow-review",),
            observed_at=NOW,
        ),
    )


def observation() -> ApprovedCognitiveObservation:
    return ApprovedCognitiveObservation(
        observation_id="observation-shadow-runtime",
        summary="approved local shadow-runtime observation",
        belief_statement="shadow runtime readiness: reviewable",
        belief_confidence=0.86,
        uncertainty_subject="shadow runtime readiness",
        uncertainty_score=0.35,
        world_state=world_state("state-before", readiness="draft", uncertainty=0.7),
        evidence_refs=("aion://aion-199/observation/shadow-runtime",),
        operator_approved=True,
        synthetic_or_redacted=True,
        observed_at=NOW,
    )


def goal() -> StrategicGoal:
    return StrategicGoal(
        goal_id="goal-shadow-runtime-review",
        description="Produce bounded local runtime evidence for operator review",
        priority=80,
        success_criteria=("operator review evidence returned",),
        required_state_features={"readiness": "reviewable"},
        evidence_refs=("aion://aion-199/goal/shadow-runtime-review",),
        created_at=NOW,
    )


def strategy() -> StrategyOption:
    return StrategyOption(
        strategy_id="strategy-local-shadow-review",
        goal_id="goal-shadow-runtime-review",
        title="Local shadow review",
        rationale="Use only bounded local proposals and review evidence",
        actions=(action(),),
        expected_information_gain=0.55,
        expected_goal_progress=0.9,
        policy_eligible=True,
        resource_budget={"cycles": 1},
        evidence_refs=("aion://aion-199/strategy/local-shadow-review",),
        created_at=NOW,
    )


def information_need() -> InformationNeed:
    return InformationNeed(
        need_id="need-shadow-runtime-readiness",
        decision_id="decision-shadow-runtime-review",
        subject="shadow runtime readiness",
        decision_context="Select the next bounded local evidence request",
        current_uncertainty=0.75,
        target_uncertainty=0.2,
        decision_relevance=0.9,
        urgency=0.6,
        evidence_refs=("aion://aion-199/information/need",),
        created_at=NOW,
    )


def memory_ref(
    episode_id: str,
    *,
    minutes: int,
    confidence: float = 0.9,
) -> EpisodicMemoryReference:
    return EpisodicMemoryReference(
        episode_id=episode_id,
        source="aion-199-fixture",
        content_summary=f"{episode_id} review evidence",
        occurred_at=NOW + timedelta(minutes=minutes),
        salience_tags=("concept:shadow runtime", "procedure:operator review"),
        evidence_refs=(f"aion://aion-199/memory/{episode_id}",),
        importance=0.9,
        confidence=confidence,
        retention_required=True,
        metadata={
            "semantic_statement": "shadow runtime evidence remains review only",
            "step": "return operator review evidence",
            "outcome": "success",
        },
    )


def learning_observation(
    episode_id: str,
    *,
    confidence: float = 0.9,
) -> ContinualLearningObservation:
    return ContinualLearningObservation(
        observation_id=f"observation-{episode_id}",
        source="aion-199-learning-fixture",
        summary=f"{episode_id} learning evidence",
        signal_tags=("policy:shadow-runtime",),
        evidence_refs=(f"aion://aion-199/learning/{episode_id}",),
        confidence=confidence,
        observed_at=NOW,
        metadata={"step": "review bounded local evidence"},
    )


def learning_episode(
    episode_id: str,
    *,
    protected_holdout: bool = False,
    minutes: int = 0,
) -> LearningEpisode:
    return LearningEpisode(
        episode_id=episode_id,
        observations=(learning_observation(episode_id),),
        outcome_label="success",
        baseline_ref="baseline://aion-199/immutable-baseline",
        policy_ref="policy://aion-199/promotion-policy",
        evidence_refs=(f"aion://aion-199/learning/episode/{episode_id}",),
        protected_holdout=protected_holdout,
        allowed_for_replay=not protected_holdout,
        occurred_at=NOW + timedelta(minutes=minutes),
    )


def cycle_input(sequence: int = 1, *, external_action: bool = False) -> CognitiveCycleInput:
    return CognitiveCycleInput(
        cycle_id=f"cycle-shadow-runtime-{sequence}",
        sequence=sequence,
        observation=observation(),
        candidate_actions=(action(),),
        transition_evidence=transition_evidence(),
        goal=goal(),
        strategies=(strategy(),),
        information_need=information_need(),
        approved_memory_refs=(
            memory_ref("episode-memory-a", minutes=1),
            memory_ref("episode-memory-b", minutes=2),
        ),
        learning_episodes=(
            learning_episode("episode-learning-a", minutes=1),
            learning_episode("episode-learning-b", minutes=2),
            learning_episode("episode-learning-holdout", protected_holdout=True, minutes=3),
        ),
        permissions={
            "clarification": True,
            "retrieval": True,
            "observation": True,
            "experiment": True,
        },
        approved_information_refs={
            "retrieval": ("aion://aion-199/approved/retrieval",),
            "observation": ("operator-approved://aion-199/local-observation",),
            "experiment": ("synthetic://aion-199/local-experiment",),
        },
        idempotency_key=f"aion-199-cycle-{sequence}",
        external_action_requested=external_action,
        created_at=NOW,
    )


def runtime_with_session(
    *,
    session_manifest: CognitiveSessionManifest | None = None,
) -> tuple[ControlledCognitiveShadowRuntime, CognitiveSessionManifest, object]:
    repository = InMemoryCognitiveStateRepository()
    runtime = ControlledCognitiveShadowRuntime(repository=repository)
    active_manifest = session_manifest or manifest()
    session = runtime.start_session(active_manifest)
    return runtime, active_manifest, session


def test_runtime_contracts_are_fingerprinted_and_authorization_bound() -> None:
    first = manifest()
    second = manifest()

    assert first.fingerprint == second.fingerprint
    assert first.authorization_id == AUTHORIZATION_ID
    assert first.required_cycle_steps == REQUIRED_CYCLE_STEPS

    with pytest.raises(ValidationError):
        CognitiveSessionManifest(
            session_id="bad-auth",
            operator_id="operator",
            input_kind="synthetic",
            state_repository_ref="local://aion-199/state",
            authorization_id="AION-000-CA-0000",
            created_at=NOW,
        )
    with pytest.raises(ValidationError):
        ApprovedCognitiveObservation(
            observation_id="bad-production",
            summary="bad production input",
            belief_statement="bad production input",
            belief_confidence=0.8,
            uncertainty_subject="bad production input",
            uncertainty_score=0.5,
            world_state=world_state("bad-state", readiness="draft", uncertainty=0.5),
            production_input=True,
            observed_at=NOW,
        )
    with pytest.raises(ValidationError):
        cycle_input(external_action=True)


def test_runtime_executes_one_bounded_cycle_and_returns_review_evidence() -> None:
    runtime, _manifest, session = runtime_with_session()
    output = runtime.run_cycle(session, cycle_input())

    assert output.status == "operator_review_required"
    assert output.state_before.sequence == 0
    assert output.state_after.sequence == 2
    assert len(output.state_after.beliefs) == 1
    assert len(output.state_after.uncertainties) == 1
    assert output.session_state.cycle_count == 1
    assert output.session_state.state_snapshot_hash == output.state_after.content_hash

    assert len(output.world_predictions) == 1
    assert output.world_predictions[0].fail_closed is False
    assert output.workspace_snapshot.active_items
    assert output.plan.selected_branch_id == "branch-strategy-local-shadow-review"
    assert output.plan.action_execution_performed is False
    assert output.information_plan.selected_candidate_ids == (
        "candidate-gap-need-shadow-runtime-readiness-retrieval",
    )
    assert output.simulated_outcomes
    assert output.consolidation_outcome.checkpoint.operator_review_required is True
    assert len(output.learning_candidates) == 6
    assert all(not candidate.promotion_allowed for candidate in output.learning_candidates)
    assert all(
        request.status == "operator_review_required" for request in output.promotion_requests
    )
    assert all(plan.rollback_available for plan in output.rollback_plans)

    assert output.evidence.cycle_steps_completed == REQUIRED_CYCLE_STEPS
    assert output.evidence.operator_review_required is True
    assert output.evidence.forbidden_side_effects == 0
    assert output.evidence.network_calls == 0
    assert output.evidence.connector_calls == 0
    assert output.evidence.model_provider_calls == 0
    assert output.evidence.git_operations == 0
    assert output.evidence.consequential_action_execution == 0
    assert output.diagnostics.runtime_effect is False
    assert output.action_execution_performed is False
    assert output.external_effect_performed is False


def test_runtime_replay_hash_is_deterministic_for_same_inputs() -> None:
    first_runtime, _first_manifest, first_session = runtime_with_session()
    second_runtime, _second_manifest, second_session = runtime_with_session()

    first = first_runtime.run_cycle(first_session, cycle_input())
    second = second_runtime.run_cycle(second_session, cycle_input())

    assert first.evidence.deterministic_replay_hash == second.evidence.deterministic_replay_hash
    assert first.state_after.content_hash == second.state_after.content_hash
    assert first.plan.fingerprint == second.plan.fingerprint
    assert first.consolidation_outcome.checkpoint.fingerprint == (
        second.consolidation_outcome.checkpoint.fingerprint
    )


def test_runtime_rejects_stale_state_before_cycle() -> None:
    repository = InMemoryCognitiveStateRepository()
    runtime = ControlledCognitiveShadowRuntime(repository=repository)
    session = runtime.start_session(manifest())

    CognitiveStateService(repository=repository).record_payload(
        event_type="resource_state_recorded",
        payload={
            "resource_id": "resource-shadow-runtime",
            "resource_type": "cycle-budget",
            "capacity": 1.0,
            "used": 0.0,
            "pressure": "low",
            "measured_at": NOW.isoformat(),
        },
        expected_previous_sequence=0,
        provenance=CognitiveStateProvenance(
            provenance_id="provenance-external-local-state-change",
            operation_id="local-state-change",
            actor_id="operator-aion-199",
            source="aion-199-test",
            evidence_refs=("aion://aion-199/stale-state",),
            created_at=NOW,
        ),
        idempotency_key="external-local-state-change",
        event_id="event-external-local-state-change",
    )

    with pytest.raises(CognitiveRuntimeBoundaryError, match="state_changed"):
        runtime.run_cycle(session, cycle_input())


def test_runtime_kill_switch_and_budget_fail_closed() -> None:
    repository = InMemoryCognitiveStateRepository()
    runtime = ControlledCognitiveShadowRuntime(repository=repository)

    with pytest.raises(CognitiveRuntimeBoundaryError, match="kill_switch"):
        runtime.start_session(manifest(kill_switch=True))

    limited_runtime, _manifest, limited_session = runtime_with_session(
        session_manifest=manifest(max_cycles=1),
    )
    first = limited_runtime.run_cycle(limited_session, cycle_input())
    with pytest.raises(CognitiveRuntimeBoundaryError, match="budget_exceeded"):
        limited_runtime.run_cycle(first.session_state, cycle_input(sequence=2))

    incident = limited_runtime.incident(
        session_id=limited_session.session_id,
        cycle_id="cycle-shadow-runtime-2",
        reason_code="budget_exceeded",
    )
    assert incident.blocked is True
    assert incident.external_effect_performed is False
