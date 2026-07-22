"""AION-202 controlled local-offline pilot evidence tests."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts/lib"))

from cognitive_architecture_governance import (  # noqa: E402
    AION201_AUTHORIZATION_ID,
    AION201_MERGE_COMMIT,
    AION201_PR,
    AION202_CANDIDATE_ID,
    AION202_IMPLEMENTATION_BRANCH,
    AION202_PROGRAM_STATE,
    AION202_SCOPE,
    AION202_TASK_ID,
    AION202_WORKSTREAM,
    AION203_EVALUATION_ID,
    AION203_TASK_ID,
    PROGRAM_ID,
    validate_aion202_pilot_payload,
    validate_local_offline_pilot_execution,
    validate_local_offline_pilot_execution_no_go,
)

REQUIRED_FILES = (
    "docs/cognitive-architecture/tasks/AION-202.md",
    "docs/cognitive-architecture/program-ledger.json",
    "docs/cognitive-architecture/authorization-ledger.json",
    "examples/cognitive-architecture/aion-202-controlled-cognitive-pilot.json",
    "services/brain-api/tests/test_cognitive_local_offline_pilot_docs.py",
    "scripts/cognitive-local-offline-pilot-execute.py",
    "scripts/cognitive-local-offline-pilot-check.sh",
    "scripts/cognitive-local-offline-pilot-no-go-regression.sh",
    "scripts/lib/cognitive_architecture_governance.py",
)


def _json(relative: str) -> dict:
    return json.loads((ROOT / relative).read_text())


def _text(relative: str) -> str:
    return (ROOT / relative).read_text()


def test_aion_202_required_files_exist() -> None:
    for relative in REQUIRED_FILES:
        path = ROOT / relative
        assert path.is_file(), relative
        if relative.startswith("scripts/"):
            assert os.access(path, os.X_OK), f"not executable: {relative}"


def test_aion_202_task_doc_contains_required_sections_and_bindings() -> None:
    text = _text("docs/cognitive-architecture/tasks/AION-202.md")
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
        AION201_AUTHORIZATION_ID,
        str(AION201_PR),
        AION201_MERGE_COMMIT,
        AION202_TASK_ID,
        AION202_SCOPE,
        AION203_EVALUATION_ID,
        "state continuity",
        "prediction accuracy",
        "uncertainty calibration",
        "information-acquisition efficiency",
        "kill-switch evidence",
        "repository integrity",
    ):
        assert term in text


def test_aion_202_pilot_payload_records_required_evidence() -> None:
    payload = _json(
        "examples/cognitive-architecture/aion-202-controlled-cognitive-pilot.json"
    )
    validate_aion202_pilot_payload(payload, root=ROOT)

    assert payload["program_id"] == PROGRAM_ID
    assert payload["task_id"] == AION202_TASK_ID
    assert payload["record_kind"] == "implementation"
    assert payload["execution_kind"] == "controlled_local_offline_pilot"
    assert payload["authorization_id"] == AION201_AUTHORIZATION_ID
    assert payload["candidate_id"] == AION202_CANDIDATE_ID
    assert payload["scope"] == AION202_SCOPE
    assert payload["workstream"] == AION202_WORKSTREAM
    assert payload["implementation_branch"] == AION202_IMPLEMENTATION_BRANCH
    assert payload["formal_closeout_task"] == AION203_TASK_ID
    assert payload["formal_closeout_evaluation"] == AION203_EVALUATION_ID

    assert payload["pilot_executed"] is True
    assert payload["approved_pilot_sessions_executed"] is True
    assert payload["sessions_executed"] == 10
    assert payload["cycles_per_session"] == 100
    assert payload["total_cycles_executed"] == 1000
    assert payload["observed_concurrency"] <= payload["maximum_concurrency"]
    assert payload["local_state_store_path"] == "/tmp/aion-os/aion-201/pilot-state.sqlite"
    assert payload["output_directory"] == "/tmp/aion-os/aion-201/redacted-pilot-evidence"
    assert payload["committed_evidence_path"] == (
        "examples/cognitive-architecture/aion-202-controlled-cognitive-pilot.json"
    )

    metrics = payload["metrics"]
    assert metrics["state_continuity_rate"] == 1.0
    assert metrics["deterministic_replay_rate"] == 1.0
    assert metrics["prediction_accuracy"] >= 0.8
    assert metrics["uncertainty_calibration_mean_absolute_error"] >= 0.0
    assert metrics["workspace_decision_rate"] == 1.0
    assert metrics["planning_success_rate"] >= 0.8
    assert metrics["information_acquisition_efficiency"] >= 0.5
    assert metrics["information_budget_overrun_count"] == 0
    assert metrics["consolidation_quality_rate"] == 1.0
    assert metrics["learning_candidate_quality_rate"] == 1.0
    assert metrics["operator_review_load_mean_items_per_cycle"] > 0
    assert metrics["operator_review_required_rate"] == 1.0
    for key in (
        "forbidden_side_effects",
        "policy_violations",
        "safety_violations",
        "critical_memory_loss",
        "unauthorized_promotions",
        "repository_runtime_mutations",
    ):
        assert metrics[key] == 0

    kill_switch = payload["kill_switch_evidence"]
    assert kill_switch["tested_before_first_session"] is True
    assert kill_switch["kill_switch_blocked"] is True
    assert kill_switch["external_effect_performed"] is False
    assert kill_switch["operator_review_required"] is True

    repository = payload["repository_integrity"]
    assert repository["state_store_initialized"] is True
    assert repository["state_store_path"] == payload["local_state_store_path"]
    assert repository["runtime_source_mutations"] == 0
    assert repository["source_modified_by_runtime"] is False
    assert repository["git_operations_by_pilot"] == 0
    assert repository["pull_requests_created_by_pilot"] == 0
    assert repository["approvals_created_by_pilot"] == 0
    assert repository["merge_operations_by_pilot"] == 0
    assert repository["deployments_by_pilot"] == 0
    assert repository["production_traffic_used"] is False
    assert repository["external_actions_performed"] is False


def test_aion_202_ledgers_record_executed_pending_evaluation_state() -> None:
    validate_local_offline_pilot_execution(ROOT)
    validate_local_offline_pilot_execution_no_go(ROOT)

    program = _json("docs/cognitive-architecture/program-ledger.json")
    authorization = _json("docs/cognitive-architecture/authorization-ledger.json")
    assert program["program_state"] == AION202_PROGRAM_STATE
    assert program["active_cognitive_implementation_authorization"] == AION201_AUTHORIZATION_ID
    assert (
        authorization["active_cognitive_implementation_authorization"]
        == AION201_AUTHORIZATION_ID
    )
    assert program["active_cognitive_implementation_authorization_count"] == 1
    assert authorization["active_cognitive_implementation_authorization_count"] == 1

    program_auth = next(
        record
        for record in program["records"]
        if record.get("authorization_id") == AION201_AUTHORIZATION_ID
        and record.get("record_kind") == "authorization"
    )
    auth_record = next(
        record
        for record in authorization["records"]
        if record.get("authorization_id") == AION201_AUTHORIZATION_ID
    )
    for record in (program_auth, auth_record):
        assert record["authorization_active"] is True
        assert record["authorization_consumed"] is False
        assert record["authorization_expired"] is False
        assert record["authorization_reusable"] is False
        assert record["authorized_task"] == AION202_TASK_ID
        assert record["pilot_executed"] is True
        assert (
            record["implementation_state"]
            == "aion_202_pilot_executed_pending_aion_203_evaluation"
        )

    execution = next(
        record
        for record in program["records"]
        if record.get("record_kind") == "implementation"
        and record.get("implementation_task") == AION202_TASK_ID
    )
    assert execution["task_state"] == "pilot_executed_pending_aion_203_evaluation"
    assert execution["pilot_executed"] is True
    assert execution["sessions_executed"] == 10
    assert execution["total_cycles_executed"] == 1000
    assert execution["state_continuity_rate"] == 1.0
    assert execution["deterministic_replay_rate"] == 1.0
    assert execution["prediction_accuracy"] >= 0.8
    assert execution["planning_success_rate"] >= 0.8
    for key in (
        "forbidden_side_effects",
        "policy_violations",
        "critical_memory_loss",
        "unauthorized_promotions",
        "repository_runtime_mutations",
        "network_calls",
        "connector_calls",
        "model_provider_calls",
        "git_operations",
        "approval_creation",
        "merge_operations",
        "deployment_operations",
        "model_weight_training",
        "consequential_action_execution",
    ):
        assert execution[key] == 0


def test_aion_202_does_not_enable_runtime_surface() -> None:
    assert not (ROOT / "services/brain-api/src/aion_brain/api/cognitive_runtime.py").exists()
    for relative in (
        "services/brain-api/src/aion_brain/kernel/container.py",
        "services/brain-api/src/aion_brain/kernel/diagnostics.py",
    ):
        text = (ROOT / relative).read_text()
        assert "ControlledCognitiveShadowRuntime" not in text
        assert "aion_brain.cognitive_runtime" not in text


def test_aion_202_scripts_are_executable_and_pass() -> None:
    env = {
        **os.environ,
        "PYTEST_CURRENT_TEST": "AION-202 focused script test",
    }
    for script in (
        "scripts/cognitive-local-offline-pilot-no-go-regression.sh",
        "scripts/cognitive-local-offline-pilot-check.sh",
    ):
        path = ROOT / script
        assert path.is_file()
        assert os.access(path, os.X_OK)
        subprocess.run([str(path)], cwd=ROOT, env=env, check=True)
