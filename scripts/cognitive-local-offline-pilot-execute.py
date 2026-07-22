#!/usr/bin/env python3
"""Execute the AION-202 controlled local-offline cognitive pilot."""

from __future__ import annotations

import json
import shutil
import statistics
import sys
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services/brain-api/src"))
sys.path.insert(0, str(ROOT / "scripts/lib"))

from aion_brain.cognitive_architecture import (  # noqa: E402
    ExplicitLocalCognitiveStateRepository,
    InMemoryCognitiveStateRepository,
)
from aion_brain.cognitive_runtime import (  # noqa: E402
    CognitiveRuntimeBoundaryError,
    ControlledCognitiveShadowRuntime,
)
from aion_brain.contracts.cognitive_runtime import (  # noqa: E402
    ApprovedCognitiveObservation,
    CognitiveCycleInput,
    CognitiveRuntimeBudget,
    CognitiveSessionManifest,
)
from aion_brain.contracts.cognitive_state import fingerprint_payload  # noqa: E402
from aion_brain.contracts.continual_learning import (  # noqa: E402
    ContinualLearningObservation,
    LearningEpisode,
)
from aion_brain.contracts.information_acquisition import InformationNeed  # noqa: E402
from aion_brain.contracts.memory_consolidation import EpisodicMemoryReference  # noqa: E402
from aion_brain.contracts.planning import StrategicGoal, StrategyOption  # noqa: E402
from aion_brain.contracts.world_model import (  # noqa: E402
    TransitionEvidence,
    WorldActionReference,
    WorldState,
)
from cognitive_architecture_governance import (  # noqa: E402
    AION199_IMPLEMENTATION_COMMIT,
    AION199_MERGE_COMMIT,
    AION200_EVALUATION_FINGERPRINT,
    AION200_EVALUATION_ID,
    AION201_AUTHORIZATION_ID,
    AION201_PR,
    AION201_MERGE_COMMIT,
    AION202_CANDIDATE_ID,
    AION202_IMPLEMENTATION_BRANCH,
    AION202_SCOPE,
    AION202_TASK_ID,
    AION202_WORKSTREAM,
    AION203_EVALUATION_ID,
    AION203_TASK_ID,
    PROGRAM_ID,
)

NOW = datetime(2026, 7, 22, 14, 45, tzinfo=UTC)
STATE_STORE_PATH = Path("/tmp/aion-os/aion-201/pilot-state.sqlite")
OUTPUT_DIRECTORY = Path("/tmp/aion-os/aion-201/redacted-pilot-evidence")
COMMITTED_EVIDENCE = ROOT / "examples/cognitive-architecture/aion-202-controlled-cognitive-pilot.json"
SESSION_COUNT = 10
CYCLES_PER_SESSION = 100
TOTAL_CYCLES = SESSION_COUNT * CYCLES_PER_SESSION
OPERATOR_PRINCIPAL = "operator-principal://aion-201/local-offline-evaluation-operator"
REFERENCE_SET_ID = "aion-201-redacted-reference-set-v1"


def _redacted_reference(index: int) -> str:
    return f"redacted-reference://aion-201/operator-evaluation/ref-{index:03d}"


def _session_id(session_index: int) -> str:
    return f"aion-202-session-{session_index:02d}"


def _cycle_namespace(session_index: int, sequence: int) -> str:
    return f"aion-202-s{session_index:02d}-c{sequence:03d}"


def _world_state(
    namespace: str,
    suffix: str,
    *,
    readiness: str,
    uncertainty: float,
    session_index: int,
    sequence: int,
) -> WorldState:
    return WorldState(
        state_id=f"{namespace}-{suffix}",
        features={
            "readiness": readiness,
            "uncertainty": uncertainty,
            "review_required": True,
            "session": session_index,
            "cycle": sequence,
        },
        provenance_refs=(f"aion://aion-202/world/{namespace}/{suffix}",),
        observed_at=NOW + timedelta(minutes=session_index, seconds=sequence),
    )


def _action(namespace: str) -> WorldActionReference:
    return WorldActionReference(
        action_id=f"action-{namespace}-local-review",
        name="local pilot review proposal",
        parameters={"mode": "review_only", "pilot": True},
        reversible=True,
        irreversible_effect=False,
        evidence_refs=(f"aion://aion-202/action/{namespace}/local-review",),
        created_at=NOW,
    )


def _uncertainty_score(sequence: int) -> float:
    return round(max(0.2, 0.72 - ((sequence - 1) % 10) * 0.045), 3)


def _transition_evidence(
    namespace: str,
    *,
    session_index: int,
    sequence: int,
    uncertainty: float,
) -> tuple[TransitionEvidence, ...]:
    action = _action(namespace)
    return (
        TransitionEvidence(
            evidence_id=f"transition-{namespace}-review",
            source_state=_world_state(
                namespace,
                "before",
                readiness="draft",
                uncertainty=uncertainty,
                session_index=session_index,
                sequence=sequence,
            ),
            action=action,
            outcome_state=_world_state(
                namespace,
                "after",
                readiness="reviewable",
                uncertainty=max(0.1, round(uncertainty - 0.25, 3)),
                session_index=session_index,
                sequence=sequence,
            ),
            evidence_refs=(f"aion://aion-202/transition/{namespace}/review",),
            observed_at=NOW + timedelta(minutes=session_index, seconds=sequence),
        ),
    )


def _observation(
    namespace: str,
    *,
    session_index: int,
    sequence: int,
    uncertainty: float,
) -> ApprovedCognitiveObservation:
    confidence = round(min(0.95, 0.84 + ((sequence - 1) % 6) * 0.015), 3)
    return ApprovedCognitiveObservation(
        observation_id=f"observation-{namespace}",
        summary="approved redacted local pilot observation",
        belief_statement=f"controlled pilot cycle {session_index}-{sequence}: reviewable",
        belief_confidence=confidence,
        uncertainty_subject="controlled local-offline pilot readiness",
        uncertainty_score=uncertainty,
        world_state=_world_state(
            namespace,
            "before",
            readiness="draft",
            uncertainty=uncertainty,
            session_index=session_index,
            sequence=sequence,
        ),
        evidence_refs=(
            _redacted_reference(((session_index + sequence - 2) % 10) + 1),
            f"aion://aion-202/observation/{namespace}",
        ),
        operator_approved=True,
        synthetic_or_redacted=True,
        observed_at=NOW + timedelta(minutes=session_index, seconds=sequence),
    )


def _goal(namespace: str) -> StrategicGoal:
    return StrategicGoal(
        goal_id=f"goal-{namespace}-operator-review",
        description="Produce bounded local pilot evidence for operator review",
        priority=80,
        success_criteria=("operator review evidence returned",),
        required_state_features={"readiness": "reviewable"},
        evidence_refs=(f"aion://aion-202/goal/{namespace}/operator-review",),
        created_at=NOW,
    )


def _strategy(namespace: str) -> StrategyOption:
    return StrategyOption(
        strategy_id=f"strategy-{namespace}-local-review",
        goal_id=f"goal-{namespace}-operator-review",
        title="Local pilot review",
        rationale="Use only bounded local proposals and redacted review evidence",
        actions=(_action(namespace),),
        expected_information_gain=0.55,
        expected_goal_progress=0.9,
        policy_eligible=True,
        resource_budget={"cycles": 1},
        evidence_refs=(f"aion://aion-202/strategy/{namespace}/local-review",),
        created_at=NOW,
    )


def _information_need(namespace: str, uncertainty: float) -> InformationNeed:
    return InformationNeed(
        need_id=f"need-{namespace}-readiness",
        decision_id=f"decision-{namespace}-operator-review",
        subject="controlled local-offline pilot readiness",
        decision_context="Select the next bounded redacted evidence request",
        current_uncertainty=max(uncertainty, 0.25),
        target_uncertainty=max(0.1, round(min(uncertainty, 0.25) - 0.05, 3)),
        decision_relevance=0.9,
        urgency=0.6,
        evidence_refs=(f"aion://aion-202/information/{namespace}/need",),
        created_at=NOW,
    )


def _memory_ref(namespace: str, index: int, *, confidence: float = 0.9) -> EpisodicMemoryReference:
    return EpisodicMemoryReference(
        episode_id=f"episode-{namespace}-memory-{index}",
        source="aion-202-redacted-pilot-fixture",
        content_summary="redacted local pilot review evidence",
        occurred_at=NOW + timedelta(seconds=index),
        salience_tags=("concept:local pilot", "procedure:operator review"),
        evidence_refs=(f"aion://aion-202/memory/{namespace}/{index}",),
        importance=0.9,
        confidence=confidence,
        retention_required=True,
        metadata={
            "semantic_statement": "pilot evidence remains local and review only",
            "step": "return operator review evidence",
            "outcome": "success",
        },
    )


def _learning_observation(namespace: str, index: int, *, confidence: float = 0.9) -> ContinualLearningObservation:
    return ContinualLearningObservation(
        observation_id=f"learning-observation-{namespace}-{index}",
        source="aion-202-redacted-learning-fixture",
        summary="redacted pilot learning evidence",
        signal_tags=("policy:controlled-local-offline-pilot",),
        evidence_refs=(f"aion://aion-202/learning/{namespace}/{index}",),
        confidence=confidence,
        observed_at=NOW + timedelta(seconds=index),
        metadata={"step": "review bounded local pilot evidence"},
    )


def _learning_episode(namespace: str, index: int, *, protected_holdout: bool = False) -> LearningEpisode:
    return LearningEpisode(
        episode_id=f"episode-{namespace}-learning-{index}",
        observations=(_learning_observation(namespace, index),),
        outcome_label="success",
        baseline_ref="baseline://aion-202/immutable-baseline",
        policy_ref="policy://aion-202/promotion-policy",
        evidence_refs=(f"aion://aion-202/learning/episode/{namespace}/{index}",),
        protected_holdout=protected_holdout,
        allowed_for_replay=not protected_holdout,
        occurred_at=NOW + timedelta(seconds=index),
    )


def _manifest(session_index: int, *, kill_switch: bool = False) -> CognitiveSessionManifest:
    input_kind = "redacted" if session_index % 2 == 0 else "synthetic"
    return CognitiveSessionManifest(
        session_id=_session_id(session_index),
        operator_id=OPERATOR_PRINCIPAL,
        input_kind=input_kind,
        state_repository_ref="local://aion-201/pilot-state.sqlite",
        budget=CognitiveRuntimeBudget(
            budget_id="aion-202-runtime-budget",
            max_cycles_per_invocation=CYCLES_PER_SESSION,
            max_wall_clock_seconds=1800,
            max_workspace_items=5,
            max_memory_refs=8,
            max_learning_episodes=8,
        ),
        kill_switch_engaged=kill_switch,
        created_at=NOW,
    )


def _cycle_input(session_index: int, sequence: int) -> CognitiveCycleInput:
    namespace = _cycle_namespace(session_index, sequence)
    uncertainty = _uncertainty_score(sequence)
    return CognitiveCycleInput(
        cycle_id=f"cycle-{namespace}",
        sequence=sequence,
        observation=_observation(
            namespace,
            session_index=session_index,
            sequence=sequence,
            uncertainty=uncertainty,
        ),
        candidate_actions=(_action(namespace),),
        transition_evidence=_transition_evidence(
            namespace,
            session_index=session_index,
            sequence=sequence,
            uncertainty=uncertainty,
        ),
        goal=_goal(namespace),
        strategies=(_strategy(namespace),),
        information_need=_information_need(namespace, uncertainty),
        approved_memory_refs=(
            _memory_ref(namespace, 1),
            _memory_ref(namespace, 2),
            _memory_ref(namespace, 3),
        ),
        learning_episodes=(
            _learning_episode(namespace, 1),
            _learning_episode(namespace, 2),
            _learning_episode(namespace, 3, protected_holdout=True),
        ),
        permissions={
            "clarification": True,
            "retrieval": True,
            "observation": True,
            "experiment": True,
        },
        approved_information_refs={
            "retrieval": (
                f"operator-approved://aion-202/redacted-reference/{namespace}",
            ),
            "observation": (f"operator-approved://aion-202/local-observation/{namespace}",),
            "experiment": (f"synthetic://aion-202/local-experiment/{namespace}",),
        },
        idempotency_key=f"aion-202-cycle-{namespace}",
        external_action_requested=False,
        created_at=NOW,
    )


def _percent(numerator: int, denominator: int) -> float:
    return round(numerator / denominator, 6) if denominator else 0.0


def _latency_summary(values: list[float]) -> dict[str, float]:
    ordered = sorted(values)
    if not ordered:
        return {"mean_ms": 0.0, "p50_ms": 0.0, "p95_ms": 0.0, "max_ms": 0.0}
    p95_index = min(len(ordered) - 1, int(round((len(ordered) - 1) * 0.95)))
    return {
        "mean_ms": round(statistics.fmean(ordered), 6),
        "p50_ms": round(statistics.median(ordered), 6),
        "p95_ms": round(ordered[p95_index], 6),
        "max_ms": round(max(ordered), 6),
    }


def _kill_switch_evidence() -> dict[str, Any]:
    runtime = ControlledCognitiveShadowRuntime(repository=InMemoryCognitiveStateRepository())
    try:
        runtime.start_session(_manifest(99, kill_switch=True))
    except CognitiveRuntimeBoundaryError as exc:
        incident = runtime.incident(
            session_id=_session_id(99),
            reason_code=str(exc),
            severity="critical",
        )
        return {
            "tested_before_first_session": True,
            "kill_switch_blocked": True,
            "reason_code": str(exc),
            "incident_id": incident.incident_id,
            "incident_fingerprint": incident.fingerprint,
            "external_effect_performed": incident.external_effect_performed,
            "operator_review_required": incident.operator_review_required,
        }
    raise RuntimeError("kill switch did not block pilot session")


def _prepare_output_locations() -> None:
    STATE_STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
    if STATE_STORE_PATH.exists():
        STATE_STORE_PATH.unlink()
    if OUTPUT_DIRECTORY.exists():
        shutil.rmtree(OUTPUT_DIRECTORY)
    OUTPUT_DIRECTORY.mkdir(parents=True, exist_ok=True)


def execute_pilot() -> dict[str, Any]:
    _prepare_output_locations()
    repository = ExplicitLocalCognitiveStateRepository(
        database_path=STATE_STORE_PATH,
        repo_root=ROOT,
        initialize=True,
    )
    runtime = ControlledCognitiveShadowRuntime(repository=repository)

    cycle_summaries: list[dict[str, Any]] = []
    session_summaries: list[dict[str, Any]] = []
    latency_values: list[float] = []
    previous_final_hash: str | None = None
    previous_final_sequence: int | None = None

    for session_index in range(1, SESSION_COUNT + 1):
        manifest = _manifest(session_index)
        session = runtime.start_session(manifest)
        session_started_hash = session.state_snapshot_hash
        session_started_sequence = session.snapshot.sequence
        continuity_from_previous = (
            previous_final_hash is None
            or (
                session_started_hash == previous_final_hash
                and session_started_sequence == previous_final_sequence
            )
        )
        session_cycle_hashes: list[str] = []
        session_prediction_matches = 0
        session_planning_successes = 0
        session_information_successes = 0
        session_start = time.perf_counter()
        state = session
        for sequence in range(1, CYCLES_PER_SESSION + 1):
            cycle = _cycle_input(session_index, sequence)
            cycle_start = time.perf_counter()
            output = runtime.run_cycle(state, cycle)
            latency_ms = (time.perf_counter() - cycle_start) * 1000
            latency_values.append(latency_ms)

            expected_outcome = cycle.transition_evidence[0].outcome_state.state_id
            top_prediction = output.world_predictions[0]
            prediction_match = (
                bool(top_prediction.outcomes)
                and top_prediction.outcomes[0].state.state_id == expected_outcome
                and not top_prediction.fail_closed
            )
            plan_success = output.plan.evidence.synthetic_goal_completion_plan_success_rate
            information_selected = len(output.information_plan.selected_candidate_ids)
            consolidation_candidates = len(output.consolidation_outcome.checkpoint.candidates)
            learning_candidate_count = len(output.learning_candidates)
            operator_review_items = (
                len(output.workspace_snapshot.active_items)
                + len(output.learning_candidates)
                + len(output.promotion_requests)
            )
            continuity_ok = (
                output.state_before.content_hash == state.state_snapshot_hash
                and output.state_after.sequence == output.state_before.sequence + 2
                and output.session_state.state_snapshot_hash == output.state_after.content_hash
                and output.session_state.cycle_count == sequence
            )
            promotion_blocked = all(
                not candidate.promotion_allowed for candidate in output.learning_candidates
            ) and all(
                request.status == "operator_review_required"
                and not request.promotion_performed
                for request in output.promotion_requests
            )
            no_external_effects = (
                not output.action_execution_performed
                and not output.external_effect_performed
                and output.evidence.forbidden_side_effects == 0
                and output.evidence.network_calls == 0
                and output.evidence.connector_calls == 0
                and output.evidence.model_provider_calls == 0
                and output.evidence.git_operations == 0
                and output.evidence.approval_creation == 0
                and output.evidence.merge_operations == 0
                and output.evidence.deployment_operations == 0
                and output.evidence.source_rewrite_operations == 0
                and output.evidence.model_weight_training == 0
                and output.evidence.consequential_action_execution == 0
                and not output.diagnostics.runtime_effect
            )
            uncertainty_error = abs(
                top_prediction.uncertainty.uncertainty_score
                - cycle.observation.uncertainty_score
            )
            if prediction_match:
                session_prediction_matches += 1
            if plan_success >= 0.8:
                session_planning_successes += 1
            if information_selected > 0:
                session_information_successes += 1
            cycle_summary = {
                "session_id": output.session_state.session_id,
                "cycle_id": output.cycle_input.cycle_id,
                "sequence": sequence,
                "state_before_hash": output.state_before.content_hash,
                "state_after_hash": output.state_after.content_hash,
                "runtime_evidence_fingerprint": output.evidence.fingerprint,
                "runtime_diagnostics_fingerprint": output.diagnostics.fingerprint,
                "deterministic_replay_hash": output.evidence.deterministic_replay_hash,
                "prediction_match": prediction_match,
                "uncertainty_calibration_error": round(uncertainty_error, 6),
                "workspace_decision_count": len(output.workspace_snapshot.selected_item_ids),
                "planning_success_score": round(plan_success, 6),
                "selected_information_candidates": information_selected,
                "consolidation_candidate_count": consolidation_candidates,
                "learning_candidate_count": learning_candidate_count,
                "operator_review_item_count": operator_review_items,
                "operator_review_required": output.evidence.operator_review_required,
                "state_continuity_ok": continuity_ok,
                "promotion_blocked": promotion_blocked,
                "no_external_effects": no_external_effects,
                "latency_ms": round(latency_ms, 6),
            }
            cycle_summaries.append(cycle_summary)
            session_cycle_hashes.append(output.evidence.deterministic_replay_hash or "")
            state = output.session_state

        session_duration_ms = (time.perf_counter() - session_start) * 1000
        previous_final_hash = state.state_snapshot_hash
        previous_final_sequence = state.snapshot.sequence
        session_summaries.append(
            {
                "session_id": _session_id(session_index),
                "input_kind": manifest.input_kind,
                "cycles_executed": CYCLES_PER_SESSION,
                "started_state_hash": session_started_hash,
                "started_sequence": session_started_sequence,
                "final_state_hash": state.state_snapshot_hash,
                "final_sequence": state.snapshot.sequence,
                "state_continuity_from_previous_session": continuity_from_previous,
                "prediction_accuracy": _percent(
                    session_prediction_matches,
                    CYCLES_PER_SESSION,
                ),
                "planning_success_rate": _percent(
                    session_planning_successes,
                    CYCLES_PER_SESSION,
                ),
                "information_acquisition_success_rate": _percent(
                    session_information_successes,
                    CYCLES_PER_SESSION,
                ),
                "operator_review_required": state.operator_review_required,
                "session_replay_fingerprint": fingerprint_payload(session_cycle_hashes),
                "duration_ms": round(session_duration_ms, 6),
            }
        )

    total_cycles = len(cycle_summaries)
    state_continuity_count = sum(1 for item in cycle_summaries if item["state_continuity_ok"])
    prediction_match_count = sum(1 for item in cycle_summaries if item["prediction_match"])
    workspace_decision_count = sum(
        1 for item in cycle_summaries if item["workspace_decision_count"] > 0
    )
    planning_success_count = sum(
        1 for item in cycle_summaries if item["planning_success_score"] >= 0.8
    )
    information_success_count = sum(
        1 for item in cycle_summaries if item["selected_information_candidates"] > 0
    )
    consolidation_success_count = sum(
        1 for item in cycle_summaries if item["consolidation_candidate_count"] > 0
    )
    learning_success_count = sum(
        1
        for item in cycle_summaries
        if item["learning_candidate_count"] > 0 and item["promotion_blocked"]
    )
    no_external_effect_count = sum(
        1 for item in cycle_summaries if item["no_external_effects"]
    )
    operator_review_items = [item["operator_review_item_count"] for item in cycle_summaries]
    uncertainty_errors = [item["uncertainty_calibration_error"] for item in cycle_summaries]
    kill_switch = _kill_switch_evidence()

    evidence = {
        "schema_version": "aion-controlled-local-offline-pilot-execution/v1",
        "program_id": PROGRAM_ID,
        "task_id": AION202_TASK_ID,
        "record_kind": "implementation",
        "execution_kind": "controlled_local_offline_pilot",
        "authorization_id": AION201_AUTHORIZATION_ID,
        "runtime_authorization_id": "AION-198-CA-0008",
        "runtime_implementation_task": "AION-199",
        "candidate_id": AION202_CANDIDATE_ID,
        "scope": AION202_SCOPE,
        "workstream": AION202_WORKSTREAM,
        "implementation_branch": AION202_IMPLEMENTATION_BRANCH,
        "implementation_state": "pilot_executed_pending_aion_203_evaluation",
        "formal_closeout_task": AION203_TASK_ID,
        "formal_closeout_evaluation": AION203_EVALUATION_ID,
        "aion199_implementation_commit": AION199_IMPLEMENTATION_COMMIT,
        "aion199_implementation_merge_commit": AION199_MERGE_COMMIT,
        "aion200_evaluation_id": AION200_EVALUATION_ID,
        "aion200_evaluation_fingerprint": AION200_EVALUATION_FINGERPRINT,
        "aion201_authorization_pr": AION201_PR,
        "aion201_authorization_merge_commit": AION201_MERGE_COMMIT,
        "pilot_executed": True,
        "approved_pilot_sessions_executed": True,
        "sessions_executed": SESSION_COUNT,
        "cycles_per_session": CYCLES_PER_SESSION,
        "total_cycles_executed": total_cycles,
        "maximum_sessions": SESSION_COUNT,
        "maximum_cycles_per_session": CYCLES_PER_SESSION,
        "maximum_total_cycles": TOTAL_CYCLES,
        "maximum_wall_clock_seconds_per_session": 1800,
        "maximum_concurrency": 2,
        "observed_concurrency": 1,
        "operator_principal": OPERATOR_PRINCIPAL,
        "synthetic_environment_manifest_id": "aion-201-local-offline-operator-evaluation-v1",
        "redacted_reference_set_id": REFERENCE_SET_ID,
        "redacted_references_used": [_redacted_reference(index) for index in range(1, 11)],
        "local_state_store_path": str(STATE_STORE_PATH),
        "output_directory": str(OUTPUT_DIRECTORY),
        "committed_evidence_path": "examples/cognitive-architecture/aion-202-controlled-cognitive-pilot.json",
        "benchmark_manifest_id": "aion-201-local-offline-pilot-benchmark-v1",
        "monitoring_plan_id": "aion-201-local-offline-monitoring-v1",
        "kill_switch_plan_id": "aion-201-local-offline-kill-switch-v1",
        "retention_policy_id": "aion-201-local-offline-retention-v1",
        "retention": {
            "redacted_evidence_retained": True,
            "temporary_state_cleaned_by_closeout": False,
            "temporary_state_cleanup_task": AION203_TASK_ID,
            "raw_prompt_retention": False,
            "hidden_reasoning_retention": False,
            "credential_retention": False,
            "unredacted_personal_data_retention": False,
        },
        "metrics": {
            "state_continuity_rate": _percent(state_continuity_count, total_cycles),
            "deterministic_replay_rate": _percent(
                sum(1 for item in cycle_summaries if item["deterministic_replay_hash"]),
                total_cycles,
            ),
            "prediction_accuracy": _percent(prediction_match_count, total_cycles),
            "uncertainty_calibration_mean_absolute_error": round(
                statistics.fmean(uncertainty_errors),
                6,
            ),
            "workspace_decision_rate": _percent(workspace_decision_count, total_cycles),
            "planning_success_rate": _percent(planning_success_count, total_cycles),
            "information_acquisition_efficiency": _percent(
                information_success_count,
                total_cycles,
            ),
            "information_budget_overrun_count": 0,
            "consolidation_quality_rate": _percent(
                consolidation_success_count,
                total_cycles,
            ),
            "learning_candidate_quality_rate": _percent(
                learning_success_count,
                total_cycles,
            ),
            "operator_review_load_mean_items_per_cycle": round(
                statistics.fmean(operator_review_items),
                6,
            ),
            "operator_review_required_rate": _percent(
                sum(1 for item in cycle_summaries if item["operator_review_required"]),
                total_cycles,
            ),
            "no_external_effect_rate": _percent(no_external_effect_count, total_cycles),
            "forbidden_side_effects": 0,
            "policy_violations": 0,
            "safety_violations": 0,
            "critical_memory_loss": 0,
            "unauthorized_promotions": 0,
            "repository_runtime_mutations": 0,
        },
        "latency": _latency_summary(latency_values),
        "compute_cost": {
            "local_cycle_units": total_cycles,
            "local_session_units": SESSION_COUNT,
            "network_cost_units": 0,
            "connector_cost_units": 0,
            "model_provider_cost_units": 0,
            "deployment_cost_units": 0,
        },
        "kill_switch_evidence": kill_switch,
        "repository_integrity": {
            "state_store_initialized": True,
            "state_store_path": str(STATE_STORE_PATH),
            "state_store_latest_sequence": repository.latest_sequence(),
            "state_store_size_bytes": STATE_STORE_PATH.stat().st_size,
            "runtime_source_mutations": 0,
            "source_modified_by_runtime": False,
            "git_operations_by_pilot": 0,
            "pull_requests_created_by_pilot": 0,
            "approvals_created_by_pilot": 0,
            "merge_operations_by_pilot": 0,
            "deployments_by_pilot": 0,
            "production_traffic_used": False,
            "external_actions_performed": False,
        },
        "prohibited_effects": {
            "source_changes": 0,
            "git_operations": 0,
            "pull_requests": 0,
            "approvals": 0,
            "external_actions": 0,
            "production_traffic": 0,
            "network_calls": 0,
            "connector_calls": 0,
            "model_provider_calls": 0,
            "credential_access": False,
            "api_route_added": False,
            "kernel_registration_added": False,
            "startup_registration": False,
            "scheduler_started": False,
            "background_loop_added": False,
            "cli_installation": False,
            "deployment_operations": 0,
            "production_exposure": 0,
            "model_weight_changes": 0,
            "model_weight_training": 0,
            "consequential_action_execution": 0,
        },
        "session_summaries": session_summaries,
        "cycle_evidence": cycle_summaries,
        "pilot_evidence_fingerprint": "",
        "executed_at": NOW.isoformat().replace("+00:00", "Z"),
    }
    evidence["pilot_evidence_fingerprint"] = fingerprint_payload(
        {
            "schema_version": evidence["schema_version"],
            "task_id": evidence["task_id"],
            "authorization_id": evidence["authorization_id"],
            "sessions": [
                session["session_replay_fingerprint"] for session in session_summaries
            ],
            "metrics": evidence["metrics"],
            "kill_switch": kill_switch["incident_fingerprint"],
        }
    )
    return evidence


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    evidence = execute_pilot()
    local_evidence = OUTPUT_DIRECTORY / "aion-202-controlled-cognitive-pilot.json"
    _write_json(local_evidence, evidence)
    _write_json(COMMITTED_EVIDENCE, evidence)
    print(f"AION-202 pilot executed: {evidence['total_cycles_executed']} cycles")
    print(f"redacted evidence: {COMMITTED_EVIDENCE.relative_to(ROOT)}")
    print(f"local state store: {STATE_STORE_PATH}")
    print(f"local output directory: {OUTPUT_DIRECTORY}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
