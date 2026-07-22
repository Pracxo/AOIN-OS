"""Controlled local-offline integrated cognitive shadow runtime."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import UTC, datetime

from aion_brain.cognitive_architecture import CognitiveStateRepository, CognitiveStateService
from aion_brain.continual_learning import (
    CandidateLearningService,
    CandidatePromotionPolicy,
    CatastrophicForgettingEvaluator,
    ExperienceReplayService,
    LearningBenchmarkEvaluator,
    LearningRollbackService,
)
from aion_brain.contracts.cognitive_runtime import (
    REQUIRED_CYCLE_STEPS,
    ApprovedCognitiveObservation,
    CognitiveCycleInput,
    CognitiveCycleOutput,
    CognitiveRuntimeDiagnostics,
    CognitiveRuntimeEvidence,
    CognitiveRuntimeIncident,
    CognitiveSessionManifest,
    CognitiveSessionState,
    IncidentSeverity,
)
from aion_brain.contracts.cognitive_state import (
    BeliefRecord,
    CognitiveStateProvenance,
    CognitiveStateSnapshot,
    ObservedActionEffect,
    UncertaintyRecord,
)
from aion_brain.contracts.continual_learning import (
    LearningCandidate,
    LearningEpisode,
    LearningEvaluation,
    LearningRollbackPlan,
    PromotionRequest,
)
from aion_brain.contracts.memory_consolidation import EpisodicMemoryReference
from aion_brain.contracts.workspace import (
    CognitiveCycleState,
    SalienceVector,
    SpecialistBid,
    WorkspaceItem,
    WorkspaceSnapshot,
)
from aion_brain.contracts.world_model import TransitionPrediction
from aion_brain.information_acquisition import InformationAcquisitionPlanner
from aion_brain.memory_consolidation import ConsolidationService
from aion_brain.planning import StrategicPlanner
from aion_brain.world_model import OutcomePredictor, ProbabilisticTransitionModel

GENERATED_AT = datetime(1970, 1, 1, tzinfo=UTC)


class CognitiveRuntimeBoundaryError(RuntimeError):
    """Raised when the shadow runtime rejects an invocation fail-closed."""


class ControlledCognitiveShadowRuntime:
    """Run one bounded local cognitive cycle under AION-198 authorization."""

    def __init__(
        self,
        *,
        repository: CognitiveStateRepository,
        state_service: CognitiveStateService | None = None,
    ) -> None:
        self._state_service = state_service or CognitiveStateService(repository=repository)

    def start_session(self, manifest: CognitiveSessionManifest) -> CognitiveSessionState:
        """Load approved local state for an explicit operator invocation."""

        if manifest.kill_switch_engaged:
            raise CognitiveRuntimeBoundaryError("cognitive_runtime_kill_switch_engaged")
        snapshot = self._state_service.current_snapshot()
        return CognitiveSessionState(
            session_id=manifest.session_id,
            manifest=manifest,
            snapshot=snapshot,
            state_snapshot_hash=snapshot.content_hash or "",
            status="ready",
            cycle_count=0,
            approved_state_loaded=True,
            persisted_approved_local_state=True,
            operator_review_required=True,
            created_at=GENERATED_AT,
        )

    def run_cycle(
        self,
        session_state: CognitiveSessionState,
        cycle_input: CognitiveCycleInput,
    ) -> CognitiveCycleOutput:
        """Run one deterministic local shadow cycle and return review evidence."""

        self._validate_cycle_boundary(session_state, cycle_input)
        before = self._state_service.current_snapshot()
        self._assert_snapshot_matches_session(before, session_state)

        belief_snapshot = self._record_belief(before, session_state, cycle_input)
        after = self._record_uncertainty(belief_snapshot, session_state, cycle_input)

        memory_refs = _bounded_memory_refs(
            cycle_input.approved_memory_refs,
            limit=session_state.manifest.budget.max_memory_refs,
        )
        model = ProbabilisticTransitionModel(evidence=cycle_input.transition_evidence)
        predictions = OutcomePredictor(model).compare_actions(
            cycle_input.observation.world_state,
            cycle_input.candidate_actions,
        )
        workspace_cycle = _workspace_cycle(session_state, cycle_input, predictions, memory_refs)
        workspace_snapshot = _require_workspace_snapshot(workspace_cycle)
        plan = StrategicPlanner().create_plan(
            goal=cycle_input.goal,
            start_state=cycle_input.observation.world_state,
            strategies=cycle_input.strategies,
            model=model,
            plan_id=f"plan-{cycle_input.cycle_id}",
        )
        information_plan = InformationAcquisitionPlanner().create_plan(
            need=cycle_input.information_need,
            permissions=cycle_input.permissions,
            approved_refs=cycle_input.approved_information_refs,
            plan_id=f"information-{cycle_input.cycle_id}",
        )
        simulated_outcomes = _simulated_outcomes(cycle_input, predictions)
        consolidation_outcome = ConsolidationService().run(
            memory_refs,
            batch_id=f"replay-{cycle_input.cycle_id}",
            max_items=min(session_state.manifest.budget.max_memory_refs, len(memory_refs)),
            outcome_id=f"consolidation-{cycle_input.cycle_id}",
        )
        (
            learning_candidates,
            learning_evaluations,
            promotion_requests,
            rollback_plans,
        ) = _learning_outputs(
            cycle_input.learning_episodes,
            cycle_id=cycle_input.cycle_id,
            max_episodes=session_state.manifest.budget.max_learning_episodes,
        )

        next_state = CognitiveSessionState(
            session_id=session_state.session_id,
            manifest=session_state.manifest,
            snapshot=after,
            state_snapshot_hash=after.content_hash or "",
            status="operator_review_required",
            cycle_count=session_state.cycle_count + 1,
            last_cycle_id=cycle_input.cycle_id,
            approved_state_loaded=True,
            persisted_approved_local_state=True,
            operator_review_required=True,
            created_at=GENERATED_AT,
        )
        evidence = CognitiveRuntimeEvidence(
            evidence_id=f"runtime-evidence-{cycle_input.cycle_id}",
            session_id=session_state.session_id,
            cycle_id=cycle_input.cycle_id,
            state_before_hash=before.content_hash or "",
            state_after_hash=after.content_hash or "",
            workspace_snapshot_hash=workspace_snapshot.snapshot_hash or "",
            plan_fingerprint=plan.fingerprint or "",
            information_plan_fingerprint=information_plan.fingerprint or "",
            consolidation_checkpoint_fingerprint=(
                consolidation_outcome.checkpoint.fingerprint or ""
            ),
            learning_candidate_ids=tuple(
                candidate.candidate_id for candidate in learning_candidates
            ),
            simulated_outcome_ids=tuple(
                outcome.observed_effect_id for outcome in simulated_outcomes
            ),
            created_at=GENERATED_AT,
        )
        diagnostics = CognitiveRuntimeDiagnostics(
            diagnostics_id=f"runtime-diagnostics-{cycle_input.cycle_id}",
            session_id=session_state.session_id,
            cycle_id=cycle_input.cycle_id,
            status="operator_review_required",
            cycle_steps_completed=REQUIRED_CYCLE_STEPS,
            cycle_count=next_state.cycle_count,
            operator_review_required=True,
            created_at=GENERATED_AT,
        )
        return CognitiveCycleOutput(
            session_state=next_state,
            cycle_input=cycle_input,
            state_before=before,
            state_after=after,
            world_predictions=predictions,
            workspace_snapshot=workspace_snapshot,
            workspace_cycle=workspace_cycle,
            plan=plan,
            information_plan=information_plan,
            simulated_outcomes=simulated_outcomes,
            consolidation_outcome=consolidation_outcome,
            learning_candidates=learning_candidates,
            learning_evaluations=learning_evaluations,
            promotion_requests=promotion_requests,
            rollback_plans=rollback_plans,
            evidence=evidence,
            diagnostics=diagnostics,
            incidents=(),
            status="operator_review_required",
            created_at=GENERATED_AT,
        )

    def incident(
        self,
        *,
        session_id: str,
        reason_code: str,
        cycle_id: str | None = None,
        severity: IncidentSeverity = "high",
    ) -> CognitiveRuntimeIncident:
        """Create a sanitized fail-closed incident record without side effects."""

        return CognitiveRuntimeIncident(
            incident_id=f"runtime-incident-{session_id}-{reason_code}",
            session_id=session_id,
            cycle_id=cycle_id,
            severity=severity,
            reason_code=reason_code,
            blocked=True,
            operator_review_required=True,
            external_effect_performed=False,
            created_at=GENERATED_AT,
        )

    def _validate_cycle_boundary(
        self,
        session_state: CognitiveSessionState,
        cycle_input: CognitiveCycleInput,
    ) -> None:
        manifest = session_state.manifest
        if manifest.kill_switch_engaged or session_state.kill_switch_engaged:
            raise CognitiveRuntimeBoundaryError("cognitive_runtime_kill_switch_engaged")
        if session_state.status not in {"ready", "operator_review_required"}:
            raise CognitiveRuntimeBoundaryError("cognitive_runtime_session_not_ready")
        if cycle_input.sequence != session_state.cycle_count + 1:
            raise CognitiveRuntimeBoundaryError("cognitive_runtime_cycle_sequence_mismatch")
        if session_state.cycle_count >= manifest.budget.max_cycles_per_invocation:
            raise CognitiveRuntimeBoundaryError("cognitive_runtime_budget_exceeded")
        if len(cycle_input.approved_memory_refs) > manifest.budget.max_memory_refs:
            raise CognitiveRuntimeBoundaryError("cognitive_runtime_memory_budget_exceeded")
        if len(cycle_input.learning_episodes) > manifest.budget.max_learning_episodes:
            raise CognitiveRuntimeBoundaryError("cognitive_runtime_learning_budget_exceeded")

    def _assert_snapshot_matches_session(
        self,
        snapshot: CognitiveStateSnapshot,
        session_state: CognitiveSessionState,
    ) -> None:
        if snapshot.content_hash != session_state.state_snapshot_hash:
            raise CognitiveRuntimeBoundaryError("cognitive_runtime_state_changed_before_cycle")
        if snapshot.sequence != session_state.snapshot.sequence:
            raise CognitiveRuntimeBoundaryError("cognitive_runtime_state_sequence_changed")

    def _record_belief(
        self,
        snapshot: CognitiveStateSnapshot,
        session_state: CognitiveSessionState,
        cycle_input: CognitiveCycleInput,
    ) -> CognitiveStateSnapshot:
        observation = cycle_input.observation
        belief = BeliefRecord(
            belief_id=f"belief-{observation.observation_id}",
            statement=observation.belief_statement,
            confidence=observation.belief_confidence,
            source_refs=observation.evidence_refs,
            revision_sequence=1,
            created_at=GENERATED_AT,
            updated_at=GENERATED_AT,
        )
        result = self._state_service.record_payload(
            event_type="belief_recorded",
            payload=belief.model_dump(mode="json"),
            expected_previous_sequence=snapshot.sequence,
            provenance=_provenance(session_state, cycle_input, "belief_recorded"),
            idempotency_key=f"{cycle_input.idempotency_key}:belief",
            event_id=f"event-{cycle_input.cycle_id}-belief",
        )
        return result.snapshot

    def _record_uncertainty(
        self,
        snapshot: CognitiveStateSnapshot,
        session_state: CognitiveSessionState,
        cycle_input: CognitiveCycleInput,
    ) -> CognitiveStateSnapshot:
        observation = cycle_input.observation
        previous = _previous_uncertainty(snapshot, observation.uncertainty_subject)
        direction = "unchanged"
        if previous is not None and observation.uncertainty_score > previous:
            direction = "increased"
        elif previous is not None and observation.uncertainty_score < previous:
            direction = "reduced"
        uncertainty = UncertaintyRecord(
            uncertainty_id=f"uncertainty-{observation.observation_id}",
            subject=observation.uncertainty_subject,
            uncertainty_score=observation.uncertainty_score,
            direction=direction,  # type: ignore[arg-type]
            rationale="approved local observation updated bounded uncertainty",
            evidence_refs=observation.evidence_refs,
            updated_at=GENERATED_AT,
        )
        result = self._state_service.record_payload(
            event_type="uncertainty_recorded",
            payload=uncertainty.model_dump(mode="json"),
            expected_previous_sequence=snapshot.sequence,
            provenance=_provenance(session_state, cycle_input, "uncertainty_recorded"),
            idempotency_key=f"{cycle_input.idempotency_key}:uncertainty",
            event_id=f"event-{cycle_input.cycle_id}-uncertainty",
        )
        return result.snapshot


def _provenance(
    session_state: CognitiveSessionState,
    cycle_input: CognitiveCycleInput,
    operation_id: str,
) -> CognitiveStateProvenance:
    return CognitiveStateProvenance(
        provenance_id=f"provenance-{cycle_input.cycle_id}-{operation_id}",
        operation_id=operation_id,
        actor_id=session_state.manifest.operator_id,
        source="aion-199-cognitive-shadow-runtime",
        evidence_refs=cycle_input.observation.evidence_refs,
        redaction_applied=True,
        runtime_effect=False,
        source_modified=False,
        git_mutated=False,
        pull_request_created=False,
        approval_created=False,
        merged=False,
        production_exposure=False,
        model_weights_changed=False,
        created_at=GENERATED_AT,
    )


def _previous_uncertainty(snapshot: CognitiveStateSnapshot, subject: str) -> float | None:
    normalized = subject.strip().lower()
    matches = [
        item.uncertainty_score
        for item in snapshot.uncertainties
        if item.subject.strip().lower() == normalized
    ]
    return matches[-1] if matches else None


def _bounded_memory_refs(
    references: tuple[EpisodicMemoryReference, ...],
    *,
    limit: int,
) -> tuple[EpisodicMemoryReference, ...]:
    return tuple(sorted(references, key=lambda item: item.episode_id))[:limit]


def _workspace_cycle(
    session_state: CognitiveSessionState,
    cycle_input: CognitiveCycleInput,
    predictions: tuple[TransitionPrediction, ...],
    memory_refs: tuple[EpisodicMemoryReference, ...],
) -> CognitiveCycleState:
    from aion_brain.workspace import CognitiveCycleCoordinator

    bids = _workspace_bids(cycle_input.observation, predictions, memory_refs)
    return CognitiveCycleCoordinator().cycle_state(
        cycle_id=cycle_input.cycle_id,
        sequence=cycle_input.sequence,
        bids=bids,
        approved_specialist_ids=session_state.manifest.approved_specialist_ids,
    )


def _workspace_bids(
    observation: ApprovedCognitiveObservation,
    predictions: Iterable[TransitionPrediction],
    memory_refs: tuple[EpisodicMemoryReference, ...],
) -> tuple[SpecialistBid, ...]:
    prediction_tuple = tuple(predictions)
    prediction_count = len(prediction_tuple)
    items = (
        WorkspaceItem(
            item_id=f"workspace-item-{observation.observation_id}",
            source_specialist_id="shadow-runtime",
            item_type="operator_context",
            content_summary=observation.summary,
            evidence_refs=observation.evidence_refs,
            metadata={"observation_id": observation.observation_id},
            created_at=GENERATED_AT,
        ),
        WorkspaceItem(
            item_id=f"workspace-item-{observation.observation_id}-prediction",
            source_specialist_id="shadow-runtime",
            item_type="world_prediction",
            content_summary=f"{prediction_count} local world-model prediction(s)",
            evidence_refs=tuple(
                prediction.fingerprint or prediction.prediction_id
                for prediction in prediction_tuple
            ),
            metadata={"prediction_count": prediction_count},
            created_at=GENERATED_AT,
        ),
        WorkspaceItem(
            item_id=f"workspace-item-{observation.observation_id}-memory",
            source_specialist_id="shadow-runtime",
            item_type="memory_signal",
            content_summary=f"{len(memory_refs)} approved memory reference(s)",
            evidence_refs=tuple(
                reference.evidence_refs[0]
                for reference in memory_refs
                if reference.evidence_refs
            ),
            metadata={"memory_reference_count": len(memory_refs)},
            created_at=GENERATED_AT,
        ),
    )
    bids: list[SpecialistBid] = []
    for index, item in enumerate(items, start=1):
        bids.append(
            SpecialistBid(
                bid_id=f"bid-{observation.observation_id}-{index}",
                specialist_id="shadow-runtime",
                item=item,
                salience=SalienceVector(
                    goal_relevance=0.8,
                    urgency=0.4,
                    novelty=0.5,
                    recurrence=0.2,
                    uncertainty=observation.uncertainty_score,
                    expected_uncertainty_reduction=0.5,
                    information_gain=0.5,
                    expected_goal_progress=0.8,
                    safety_risk=0.0,
                    resource_cost=0.1,
                    irreversibility=0.0,
                    confidence=observation.belief_confidence,
                ),
                requested_capacity_units=1,
                evidence_refs=item.evidence_refs,
                submitted_at=GENERATED_AT,
            )
        )
    return tuple(bids)


def _require_workspace_snapshot(workspace_cycle: CognitiveCycleState) -> WorkspaceSnapshot:
    active_items = workspace_cycle.broadcast.selected_items if workspace_cycle.broadcast else ()
    decision = workspace_cycle.decision
    deferred_bids = decision.deferred_bids if decision is not None else ()
    return WorkspaceSnapshot(
        snapshot_id=f"workspace-snapshot-{workspace_cycle.cycle_id}",
        cycle_id=workspace_cycle.cycle_id,
        sequence=workspace_cycle.sequence,
        active_items=active_items,
        selected_item_ids=tuple(item.item_id for item in active_items),
        deferred_item_ids=tuple(bid.item.item_id for bid in deferred_bids),
        approved_specialist_ids=(
            workspace_cycle.broadcast.approved_specialist_ids
            if workspace_cycle.broadcast
            else ()
        ),
        audit_events=workspace_cycle.audit_events,
        created_at=GENERATED_AT,
    )


def _simulated_outcomes(
    cycle_input: CognitiveCycleInput,
    predictions: tuple[TransitionPrediction, ...],
) -> tuple[ObservedActionEffect, ...]:
    outcomes: list[ObservedActionEffect] = []
    for index, prediction in enumerate(predictions, start=1):
        if prediction.outcomes:
            observed = f"simulated local outcome {prediction.outcomes[0].state.state_id}"
            refs = (prediction.fingerprint or prediction.prediction_id,)
        else:
            observed = "simulated local outcome failed closed"
            refs = (prediction.prediction_id,)
        outcomes.append(
            ObservedActionEffect(
                observed_effect_id=f"simulated-{cycle_input.cycle_id}-{index}",
                action_ref=prediction.action_id,
                observed_outcome=observed,
                matches_expected=bool(prediction.outcomes),
                evidence_refs=refs,
                created_at=GENERATED_AT,
            )
        )
    return tuple(outcomes)


def _learning_outputs(
    episodes: tuple[LearningEpisode, ...],
    *,
    cycle_id: str,
    max_episodes: int,
) -> tuple[
    tuple[LearningCandidate, ...],
    tuple[LearningEvaluation, ...],
    tuple[PromotionRequest, ...],
    tuple[LearningRollbackPlan, ...],
]:
    replay = ExperienceReplayService().select(
        episodes,
        sample_id=f"learning-replay-{cycle_id}",
        max_episodes=min(max_episodes, len(episodes)),
    )
    candidates = CandidateLearningService().learn(episodes, replay)
    holdout = tuple(episode for episode in episodes if episode.protected_holdout)
    forgetting = CatastrophicForgettingEvaluator()
    benchmark = LearningBenchmarkEvaluator()
    promotion = CandidatePromotionPolicy()
    rollback = LearningRollbackService()
    evaluations: list[LearningEvaluation] = []
    requests: list[PromotionRequest] = []
    rollbacks: list[LearningRollbackPlan] = []
    for candidate in candidates:
        risk = forgetting.evaluate(candidate, replay_sample=replay, holdout_episodes=holdout)
        evaluation = benchmark.evaluate(
            candidate,
            replay_sample=replay,
            forgetting_risk=risk,
        )
        evaluations.append(evaluation)
        requests.append(
            promotion.review(
                candidate,
                evaluation,
                requested_by="operator",
            )
        )
        rollbacks.append(rollback.plan(candidate))
    return tuple(candidates), tuple(evaluations), tuple(requests), tuple(rollbacks)


__all__ = [
    "CognitiveRuntimeBoundaryError",
    "ControlledCognitiveShadowRuntime",
]
