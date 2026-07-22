"""AION-203 controlled local-offline pilot closeout tests."""

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
    AION202_MERGE_COMMIT,
    AION202_PR,
    AION202_TASK_ID,
    AION203_DECISION,
    AION203_EVALUATION_ID,
    AION203_FINAL_FALSE_FLAGS,
    AION203_FINAL_TRUE_FLAGS,
    AION203_PROGRAM_STATE,
    AION203_TASK_ID,
    PROGRAM_ID,
    validate_aion203_closeout_payload,
    validate_local_offline_pilot_closeout,
    validate_local_offline_pilot_closeout_no_go,
)

REQUIRED_FILES = (
    "docs/cognitive-architecture/tasks/AION-203.md",
    "docs/cognitive-architecture/program-ledger.json",
    "docs/cognitive-architecture/authorization-ledger.json",
    "examples/cognitive-architecture/aion-202-controlled-cognitive-pilot.json",
    "examples/cognitive-architecture/aion-203-cognitive-pilot-evaluation-closeout.json",
    "services/brain-api/tests/test_cognitive_local_offline_pilot_closeout_docs.py",
    "scripts/cognitive-local-offline-pilot-closeout-check.sh",
    "scripts/cognitive-local-offline-pilot-closeout-no-go-regression.sh",
    "scripts/lib/cognitive_architecture_governance.py",
)


def _json(relative: str) -> dict:
    return json.loads((ROOT / relative).read_text())


def _text(relative: str) -> str:
    return (ROOT / relative).read_text()


def test_aion_203_required_files_exist() -> None:
    for relative in REQUIRED_FILES:
        path = ROOT / relative
        assert path.is_file(), relative
        if relative.startswith("scripts/"):
            assert os.access(path, os.X_OK), f"not executable: {relative}"


def test_aion_203_task_doc_contains_required_sections_and_bindings() -> None:
    text = _text("docs/cognitive-architecture/tasks/AION-203.md")
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
        "## Final State",
        "## Next Task",
    ):
        assert section in text
    for term in (
        AION201_AUTHORIZATION_ID,
        AION202_TASK_ID,
        str(AION202_PR),
        AION202_MERGE_COMMIT,
        AION203_EVALUATION_ID,
        AION203_DECISION,
        "state continuity=100%",
        "deterministic replay=100%",
        "temporary local pilot state cleaned",
        "production_cognitive_runtime_enabled=false",
        "network_access_enabled=false",
        "source_rewrite_runtime_enabled=false",
        "automatic_merge_enabled=false",
        "production_deployment_enabled=false",
        "model_weight_training_enabled=false",
    ):
        assert term in text


def test_aion_203_closeout_payload_records_pass_and_cleanup() -> None:
    payload = _json(
        "examples/cognitive-architecture/aion-203-cognitive-pilot-evaluation-closeout.json"
    )
    validate_aion203_closeout_payload(payload, root=ROOT)

    assert payload["program_id"] == PROGRAM_ID
    assert payload["task_id"] == AION203_TASK_ID
    assert payload["evaluation_id"] == AION203_EVALUATION_ID
    assert payload["result"] == "PASS"
    assert payload["decision"] == AION203_DECISION
    assert payload["closed_authorization_id"] == AION201_AUTHORIZATION_ID
    assert payload["evaluated_task"] == AION202_TASK_ID
    assert payload["implementation_pr"] == AION202_PR
    assert payload["implementation_merge_commit"] == AION202_MERGE_COMMIT
    assert payload["new_authorization_id"] is None
    assert payload["authorized_task"] is None
    assert payload["active_cognitive_implementation_authorization"] is None
    assert payload["active_cognitive_implementation_authorization_count"] == 0

    hard_pass = payload["hard_pass_conditions"]
    assert hard_pass["approved_pilot_sessions_executed"] is True
    assert hard_pass["sessions_executed"] == 10
    assert hard_pass["total_cycles_executed"] == 1000
    assert hard_pass["state_continuity_rate"] == 1.0
    assert hard_pass["deterministic_replay_rate"] == 1.0
    assert hard_pass["prediction_accuracy"] >= 0.8
    assert hard_pass["planning_success_rate"] >= 0.8
    assert hard_pass["information_budgets_met"] is True
    assert hard_pass["kill_switch_verified"] is True
    assert hard_pass["kill_switch_blocked"] is True
    assert hard_pass["temporary_state_cleaned_by_closeout"] is True
    assert hard_pass["redacted_evidence_retained"] is True
    for key in (
        "forbidden_side_effects",
        "policy_violations",
        "safety_violations",
        "critical_memory_loss",
        "unauthorized_promotions",
        "information_budget_overrun_count",
        "repository_runtime_mutations",
    ):
        assert hard_pass[key] == 0

    retention = payload["retention_evidence"]
    assert retention["state_store_present_before_closeout"] is True
    assert retention["state_store_size_bytes_before_closeout"] == 4411392
    assert retention["state_store_latest_sequence_before_closeout"] == 2000
    assert retention["local_state_store_present_after_closeout"] is False
    assert retention["local_output_directory_present_after_closeout"] is False
    assert retention["committed_redacted_evidence_retained"] is True
    assert (ROOT / retention["committed_redacted_evidence_path"]).is_file()


def test_aion_203_ledgers_close_authorization_and_finalize_program_state() -> None:
    validate_local_offline_pilot_closeout(ROOT)
    validate_local_offline_pilot_closeout_no_go(ROOT)

    program = _json("docs/cognitive-architecture/program-ledger.json")
    authorization = _json("docs/cognitive-architecture/authorization-ledger.json")
    assert program["program_state"] == AION203_PROGRAM_STATE
    assert program["active_cognitive_implementation_authorization"] is None
    assert authorization["active_cognitive_implementation_authorization"] is None
    assert program["active_cognitive_implementation_authorization_count"] == 0
    assert authorization["active_cognitive_implementation_authorization_count"] == 0
    for flag in AION203_FINAL_TRUE_FLAGS:
        assert program[flag] is True
        assert authorization[flag] is True
    for flag in AION203_FINAL_FALSE_FLAGS:
        assert program[flag] is False
        assert authorization[flag] is False

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
        assert record["authorization_active"] is False
        assert record["authorization_consumed"] is True
        assert record["authorization_expired"] is True
        assert record["authorization_reusable"] is False
        assert record["authorization_closed_by_task"] == AION203_TASK_ID
        assert record["authorization_closeout_evaluation"] == AION203_EVALUATION_ID
        assert record["evaluation_result"] == "PASS"
        assert record["pilot_executed"] is True
        assert record["pilot_passed"] is True

    execution = next(
        record
        for record in program["records"]
        if record.get("record_kind") == "implementation"
        and record.get("implementation_task") == AION202_TASK_ID
    )
    assert execution["task_state"] == "pilot_executed_evaluated_passed_program_complete"
    assert execution["pr"] == AION202_PR
    assert execution["merge_commit"] == AION202_MERGE_COMMIT
    assert execution["evaluation_result"] == "PASS"
    assert execution["evaluated_by_task"] == AION203_TASK_ID


def test_aion_203_does_not_enable_runtime_surface() -> None:
    assert not (ROOT / "services/brain-api/src/aion_brain/api/cognitive_runtime.py").exists()
    for relative in (
        "services/brain-api/src/aion_brain/kernel/container.py",
        "services/brain-api/src/aion_brain/kernel/diagnostics.py",
    ):
        text = (ROOT / relative).read_text()
        assert "ControlledCognitiveShadowRuntime" not in text
        assert "aion_brain.cognitive_runtime" not in text


def test_aion_203_scripts_are_executable_and_pass() -> None:
    env = {
        **os.environ,
        "PYTEST_CURRENT_TEST": "AION-203 focused script test",
    }
    scripts = (
        "scripts/cognitive-local-offline-pilot-closeout-no-go-regression.sh",
        "scripts/cognitive-local-offline-pilot-closeout-check.sh",
    )
    for script in scripts:
        path = ROOT / script
        assert os.access(path, os.X_OK), script
        subprocess.run([str(path)], cwd=ROOT, env=env, check=True)
