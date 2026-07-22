"""AION-200 cognitive shadow-runtime evaluation closeout tests."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from test_cognitive_shadow_runtime import (
    NOW,
    cycle_input,
    manifest,
)

from aion_brain.cognitive_architecture import (
    CognitiveStateService,
    InMemoryCognitiveStateRepository,
)
from aion_brain.cognitive_runtime import (
    CognitiveRuntimeBoundaryError,
    ControlledCognitiveShadowRuntime,
)
from aion_brain.contracts.cognitive_runtime import (
    REQUIRED_CYCLE_STEPS,
    CognitiveCycleInput,
)
from aion_brain.contracts.cognitive_state import CognitiveStateProvenance

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts/lib"))

from cognitive_architecture_governance import (  # noqa: E402
    AION198_AUTHORIZATION_ID,
    AION199_MERGE_COMMIT,
    AION199_PR,
    AION199_SCOPE,
    AION199_TASK_ID,
    AION200_DECISION,
    AION200_EVALUATION_ID,
    AION200_PROGRAM_STATE,
    AION200_TASK_ID,
    AION201_AUTHORIZATION_ID,
    AION201_PROGRAM_STATE,
    AION201_TASK_ID,
    AION202_PROGRAM_STATE,
    PROGRAM_ID,
    validate_aion200_evaluation_payload,
    validate_shadow_runtime_evaluation,
    validate_shadow_runtime_evaluation_no_go,
)

REQUIRED_FILES = (
    "docs/cognitive-architecture/tasks/AION-200.md",
    "docs/cognitive-architecture/program-ledger.json",
    "docs/cognitive-architecture/authorization-ledger.json",
    "examples/cognitive-architecture/aion-200-cognitive-shadow-runtime-evaluation.json",
    "services/brain-api/tests/test_cognitive_shadow_runtime_evaluation_closeout.py",
    "scripts/cognitive-shadow-runtime-evaluation-check.sh",
    "scripts/cognitive-shadow-runtime-evaluation-no-go-regression.sh",
    "scripts/lib/cognitive_architecture_governance.py",
)


def _json(relative: str) -> dict:
    return json.loads((ROOT / relative).read_text())


def _text(relative: str) -> str:
    return (ROOT / relative).read_text()


def _aion202_evidence_exists() -> bool:
    return (
        ROOT / "examples/cognitive-architecture/aion-202-controlled-cognitive-pilot.json"
    ).is_file()


def _unique_cycle(sequence: int, namespace: str):
    payload = cycle_input(sequence=sequence).model_dump()
    payload.pop("fingerprint", None)
    payload["cycle_id"] = f"cycle-{namespace}-{sequence}"
    payload["idempotency_key"] = f"{namespace}-cycle-{sequence}"
    return CognitiveCycleInput(**payload)


def _run_synthetic_cycles(count: int, *, namespace: str = "aion-200"):
    repository = InMemoryCognitiveStateRepository()
    runtime = ControlledCognitiveShadowRuntime(repository=repository)
    session = runtime.start_session(manifest())
    outputs = []
    state = session
    for sequence in range(1, count + 1):
        output = runtime.run_cycle(state, _unique_cycle(sequence, namespace))
        outputs.append(output)
        state = output.session_state
    return repository, outputs


def test_aion_200_required_files_exist() -> None:
    for relative in REQUIRED_FILES:
        path = ROOT / relative
        assert path.is_file(), relative
        if relative.startswith("scripts/"):
            assert os.access(path, os.X_OK), f"not executable: {relative}"


def test_aion_200_task_doc_contains_required_sections_and_terms() -> None:
    text = _text("docs/cognitive-architecture/tasks/AION-200.md")
    for section in (
        "## Task Purpose",
        "## Authorization ID",
        "## Exact Scope",
        "## Role Comparison",
        "## Source Boundaries",
        "## Required Contracts",
        "## Required Services",
        "## Required Tests",
        "## Required Gates",
        "## Security Invariants",
        "## Performance Limits",
        "## Completion Conditions",
        "## Next Task",
    ):
        assert section in text
    for term in (
        AION198_AUTHORIZATION_ID,
        AION199_TASK_ID,
        AION199_SCOPE,
        AION199_MERGE_COMMIT,
        AION200_EVALUATION_ID,
        AION200_DECISION,
    ):
        assert term in text


def test_aion_200_evaluation_payload_meets_hard_pass_conditions() -> None:
    payload = _json(
        "examples/cognitive-architecture/aion-200-cognitive-shadow-runtime-evaluation.json"
    )
    validate_aion200_evaluation_payload(payload)

    assert payload["program_id"] == PROGRAM_ID
    assert payload["task_id"] == AION200_TASK_ID
    assert payload["evaluation_id"] == AION200_EVALUATION_ID
    assert payload["closed_authorization_id"] == AION198_AUTHORIZATION_ID
    assert payload["evaluated_task"] == AION199_TASK_ID
    assert payload["implementation_pr"] == AION199_PR
    assert payload["implementation_merge_commit"] == AION199_MERGE_COMMIT
    assert payload["result"] == "PASS"
    assert payload["decision"] == AION200_DECISION

    metrics = payload["hard_pass_conditions"]
    assert metrics["restart_continuity_rate"] == 1.0
    assert metrics["hundred_cycle_state_persistence_rate"] == 1.0
    assert metrics["deterministic_replay_rate"] == 1.0
    assert metrics["kill_switch_block_rate"] == 1.0
    assert metrics["budget_violation_block_rate"] == 1.0
    assert metrics["corrupted_state_block_rate"] == 1.0
    assert metrics["stale_state_rejection_rate"] == 1.0
    assert metrics["concurrency_conflict_rejection_rate"] == 1.0
    assert metrics["forbidden_side_effect_count"] == 0
    assert metrics["policy_violations"] == 0
    assert metrics["unauthorized_promotions"] == 0


def test_runtime_restart_continuity_and_hundred_cycle_state_persistence() -> None:
    repository = InMemoryCognitiveStateRepository()
    first_runtime = ControlledCognitiveShadowRuntime(repository=repository)
    first_session = first_runtime.start_session(manifest())
    first_output = first_runtime.run_cycle(first_session, _unique_cycle(1, "aion-200-before"))

    restarted_runtime = ControlledCognitiveShadowRuntime(repository=repository)
    restarted_session = restarted_runtime.start_session(manifest())
    assert restarted_session.approved_state_loaded is True
    assert restarted_session.snapshot.sequence == first_output.state_after.sequence
    assert restarted_session.state_snapshot_hash == first_output.state_after.content_hash

    restarted_output = restarted_runtime.run_cycle(
        restarted_session,
        _unique_cycle(1, "aion-200-after"),
    )
    assert restarted_output.state_before.sequence == first_output.state_after.sequence
    assert restarted_output.state_after.sequence == first_output.state_after.sequence + 2

    _repository, outputs = _run_synthetic_cycles(100, namespace="aion-200-100")
    assert len(outputs) == 100
    assert outputs[-1].session_state.cycle_count == 100
    assert outputs[-1].state_after.sequence == 200
    assert outputs[-1].session_state.persisted_approved_local_state is True
    assert outputs[-1].diagnostics.cycle_steps_completed == REQUIRED_CYCLE_STEPS


def test_runtime_prediction_workspace_memory_information_and_learning_evidence() -> None:
    _repository, outputs = _run_synthetic_cycles(3, namespace="aion-200-evidence")
    output = outputs[-1]

    assert output.world_predictions
    assert all(not prediction.fail_closed for prediction in output.world_predictions)
    assert output.plan.action_execution_performed is False
    assert output.plan.selected_branch_id is not None
    assert output.workspace_snapshot.active_items
    assert output.consolidation_outcome.checkpoint.operator_review_required is True
    assert output.information_plan.selected_candidate_ids
    assert output.learning_candidates
    assert all(not candidate.promotion_allowed for candidate in output.learning_candidates)
    assert all(
        request.status == "operator_review_required" for request in output.promotion_requests
    )
    assert output.evidence.operator_review_required is True
    assert output.evidence.forbidden_side_effects == 0


def test_runtime_kill_switch_budget_corrupted_state_stale_state_and_concurrency_fail_closed(
) -> None:
    repository = InMemoryCognitiveStateRepository()
    runtime = ControlledCognitiveShadowRuntime(repository=repository)

    with pytest.raises(CognitiveRuntimeBoundaryError, match="kill_switch"):
        runtime.start_session(manifest(kill_switch=True))

    limited_runtime = ControlledCognitiveShadowRuntime(
        repository=InMemoryCognitiveStateRepository()
    )
    limited_session = limited_runtime.start_session(manifest(max_cycles=1))
    limited_output = limited_runtime.run_cycle(limited_session, _unique_cycle(1, "aion-200-budget"))
    with pytest.raises(CognitiveRuntimeBoundaryError, match="budget_exceeded"):
        limited_runtime.run_cycle(limited_output.session_state, _unique_cycle(2, "aion-200-budget"))

    corrupted_session = runtime.start_session(manifest())
    corrupted_session = corrupted_session.model_copy(update={"state_snapshot_hash": "corrupted"})
    with pytest.raises(CognitiveRuntimeBoundaryError, match="state_changed"):
        runtime.run_cycle(corrupted_session, _unique_cycle(1, "aion-200-corrupted"))

    stale_repository = InMemoryCognitiveStateRepository()
    stale_runtime = ControlledCognitiveShadowRuntime(repository=stale_repository)
    stale_session = stale_runtime.start_session(manifest())
    CognitiveStateService(repository=stale_repository).record_payload(
        event_type="resource_state_recorded",
        payload={
            "resource_id": "resource-aion-200-stale",
            "resource_type": "cycle-budget",
            "capacity": 1.0,
            "used": 0.0,
            "pressure": "low",
            "measured_at": NOW.isoformat(),
        },
        expected_previous_sequence=0,
        provenance=CognitiveStateProvenance(
            provenance_id="provenance-aion-200-stale-state",
            operation_id="local-stale-state-change",
            actor_id="operator-aion-200",
            source="aion-200-evaluation",
            evidence_refs=("aion://aion-200/stale-state",),
            created_at=NOW,
        ),
        idempotency_key="aion-200-stale-state-change",
        event_id="event-aion-200-stale-state-change",
    )
    with pytest.raises(CognitiveRuntimeBoundaryError, match="state_changed"):
        stale_runtime.run_cycle(stale_session, _unique_cycle(1, "aion-200-stale"))

    concurrent_repository = InMemoryCognitiveStateRepository()
    concurrent_runtime = ControlledCognitiveShadowRuntime(repository=concurrent_repository)
    first_session = concurrent_runtime.start_session(manifest())
    second_session = concurrent_runtime.start_session(manifest())
    concurrent_runtime.run_cycle(first_session, _unique_cycle(1, "aion-200-concurrent-a"))
    with pytest.raises(CognitiveRuntimeBoundaryError, match="state_changed"):
        concurrent_runtime.run_cycle(second_session, _unique_cycle(1, "aion-200-concurrent-b"))


def test_runtime_deterministic_replay_and_zero_external_effects() -> None:
    _first_repository, first_outputs = _run_synthetic_cycles(5, namespace="aion-200-replay")
    _second_repository, second_outputs = _run_synthetic_cycles(5, namespace="aion-200-replay")

    assert first_outputs[-1].state_after.content_hash == second_outputs[-1].state_after.content_hash
    assert first_outputs[-1].evidence.deterministic_replay_hash == (
        second_outputs[-1].evidence.deterministic_replay_hash
    )
    for output in first_outputs + second_outputs:
        assert output.action_execution_performed is False
        assert output.external_effect_performed is False
        assert output.evidence.network_calls == 0
        assert output.evidence.connector_calls == 0
        assert output.evidence.model_provider_calls == 0
        assert output.evidence.git_operations == 0
        assert output.evidence.approval_creation == 0
        assert output.evidence.merge_operations == 0
        assert output.evidence.deployment_operations == 0
        assert output.evidence.consequential_action_execution == 0
        assert output.diagnostics.runtime_effect is False


def test_aion_200_ledgers_close_aion_198_without_pilot_authorization() -> None:
    validate_shadow_runtime_evaluation(ROOT)
    validate_shadow_runtime_evaluation_no_go(ROOT)

    program = _json("docs/cognitive-architecture/program-ledger.json")
    authorization = _json("docs/cognitive-architecture/authorization-ledger.json")
    aion201_authorized = any(
        record.get("authorization_id") == AION201_AUTHORIZATION_ID
        for record in program["records"]
    )

    if _aion202_evidence_exists():
        expected_program_state = AION202_PROGRAM_STATE
    else:
        expected_program_state = (
            AION201_PROGRAM_STATE if aion201_authorized else AION200_PROGRAM_STATE
        )
    expected_active = AION201_AUTHORIZATION_ID if aion201_authorized else None
    expected_count = 1 if aion201_authorized else 0
    assert program["program_state"] == expected_program_state
    assert program["active_cognitive_implementation_authorization"] == expected_active
    assert authorization["active_cognitive_implementation_authorization"] == expected_active
    assert program["active_cognitive_implementation_authorization_count"] == expected_count
    assert authorization["active_cognitive_implementation_authorization_count"] == expected_count

    implementation = next(
        record
        for record in program["records"]
        if record.get("implementation_task") == AION199_TASK_ID
    )
    assert implementation["pr"] == AION199_PR
    assert implementation["merge_commit"] == AION199_MERGE_COMMIT
    assert implementation["task_state"] == "merged_evaluated_passed"

    closeout = next(
        record
        for record in program["records"]
        if record.get("task_id") == AION200_TASK_ID
        and record.get("evaluation_id") == AION200_EVALUATION_ID
    )
    assert closeout["result"] == "PASS"
    assert closeout["closed_authorization_id"] == AION198_AUTHORIZATION_ID
    assert closeout["new_authorization_id"] is None
    assert closeout["authorized_task"] is None
    assert closeout["recommendation"] == (
        "controlled_local_offline_cognitive_pilot_authorization_review"
    )

    closed = next(
        record
        for record in authorization["records"]
        if record["authorization_id"] == AION198_AUTHORIZATION_ID
    )
    assert closed["record_kind"] == "implementation_authorization_closeout"
    assert closed["authorization_active"] is False
    assert closed["authorization_consumed"] is True
    assert closed["authorization_expired"] is True
    assert closed["authorization_reusable"] is False
    assert closed["authorization_closed_by_task"] == AION200_TASK_ID
    assert closed["authorization_closeout_evaluation"] == AION200_EVALUATION_ID
    assert closed["implementation_pr"] == AION199_PR
    assert closed["implementation_merge_commit"] == AION199_MERGE_COMMIT
    assert closed["evaluation_result"] == "PASS"

    if aion201_authorized:
        aion201_program = next(
            record
            for record in program["records"]
            if record.get("authorization_id") == AION201_AUTHORIZATION_ID
        )
        aion201_authorization = next(
            record
            for record in authorization["records"]
            if record.get("authorization_id") == AION201_AUTHORIZATION_ID
        )
        assert aion201_program["task_id"] == AION201_TASK_ID
        assert aion201_authorization["task_id"] == AION201_TASK_ID
    else:
        assert all(
            record.get("authorization_id") != AION201_AUTHORIZATION_ID
            for record in program["records"] + authorization["records"]
        )


def test_aion_200_scripts_are_executable_and_pass() -> None:
    env = {
        **os.environ,
        "PYTEST_CURRENT_TEST": "AION-200 focused script test",
    }
    scripts = (
        "scripts/cognitive-shadow-runtime-evaluation-no-go-regression.sh",
        "scripts/cognitive-shadow-runtime-evaluation-check.sh",
    )
    for script in scripts:
        path = ROOT / script
        assert path.is_file()
        assert os.access(path, os.X_OK)
        subprocess.run([str(path)], cwd=ROOT, env=env, check=True)
