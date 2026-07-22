"""AION-201 controlled local-offline pilot authorization tests."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts/lib"))

from cognitive_architecture_governance import (  # noqa: E402
    AION199_IMPLEMENTATION_COMMIT,
    AION199_MERGE_COMMIT,
    AION200_DECISION,
    AION200_EVALUATION_FINGERPRINT,
    AION200_EVALUATION_ID,
    AION200_MERGE_COMMIT,
    AION200_PR,
    AION200_TASK_ID,
    AION201_AUTHORIZATION_ID,
    AION201_PROGRAM_STATE,
    AION201_TASK_ID,
    AION202_CANDIDATE_ID,
    AION202_IMPLEMENTATION_BRANCH,
    AION202_PROGRAM_STATE,
    AION202_SCOPE,
    AION202_TASK_ID,
    AION202_WORKSTREAM,
    AION203_EVALUATION_ID,
    AION203_PROGRAM_STATE,
    AION203_TASK_ID,
    PROGRAM_ID,
    validate_aion201_authorization_payload,
    validate_local_offline_pilot_authorization,
    validate_local_offline_pilot_authorization_no_go,
)

REQUIRED_FILES = (
    "docs/cognitive-architecture/tasks/AION-201.md",
    "docs/cognitive-architecture/program-ledger.json",
    "docs/cognitive-architecture/authorization-ledger.json",
    "examples/cognitive-architecture/aion-201-local-offline-pilot-authorization.json",
    "services/brain-api/tests/test_cognitive_local_offline_pilot_authorization_docs.py",
    "scripts/cognitive-local-offline-pilot-authorization-check.sh",
    "scripts/cognitive-local-offline-pilot-authorization-no-go-regression.sh",
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


def _aion203_closeout_exists() -> bool:
    return (
        ROOT
        / "examples/cognitive-architecture/aion-203-cognitive-pilot-evaluation-closeout.json"
    ).is_file()


def test_aion_201_required_files_exist() -> None:
    for relative in REQUIRED_FILES:
        path = ROOT / relative
        assert path.is_file(), relative
        if relative.startswith("scripts/"):
            assert os.access(path, os.X_OK), f"not executable: {relative}"


def test_aion_201_task_doc_contains_required_sections_and_bindings() -> None:
    text = _text("docs/cognitive-architecture/tasks/AION-201.md")
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
        AION199_IMPLEMENTATION_COMMIT,
        AION199_MERGE_COMMIT,
        AION200_EVALUATION_ID,
        AION200_EVALUATION_FINGERPRINT,
        AION202_TASK_ID,
        AION202_SCOPE,
        AION203_EVALUATION_ID,
    ):
        assert term in text


def test_aion_201_authorization_payload_binds_exact_pilot_contract() -> None:
    payload = _json(
        "examples/cognitive-architecture/aion-201-local-offline-pilot-authorization.json"
    )
    validate_aion201_authorization_payload(payload, root=ROOT)

    assert payload["program_id"] == PROGRAM_ID
    assert payload["task_id"] == AION201_TASK_ID
    assert payload["authorization_id"] == AION201_AUTHORIZATION_ID
    assert payload["parent_task"] == AION200_TASK_ID
    assert payload["parent_evaluation_id"] == AION200_EVALUATION_ID
    assert payload["parent_pr"] == AION200_PR
    assert payload["parent_commit"] == AION200_MERGE_COMMIT
    assert payload["parent_decision"] == AION200_DECISION
    assert payload["authorized_task"] == AION202_TASK_ID
    assert payload["implementation_branch"] == AION202_IMPLEMENTATION_BRANCH
    assert payload["candidate_id"] == AION202_CANDIDATE_ID
    assert payload["workstream"] == AION202_WORKSTREAM
    assert payload["scope"] == AION202_SCOPE
    assert payload["formal_closeout_task"] == AION203_TASK_ID
    assert payload["formal_closeout_evaluation"] == AION203_EVALUATION_ID
    assert payload["aion199_implementation_commit"] == AION199_IMPLEMENTATION_COMMIT

    aion200 = _json(
        "examples/cognitive-architecture/aion-200-cognitive-shadow-runtime-evaluation.json"
    )
    canonical = json.dumps(aion200, sort_keys=True, separators=(",", ":")).encode()
    assert hashlib.sha256(canonical).hexdigest() == AION200_EVALUATION_FINGERPRINT
    assert (
        payload["aion200_evaluation_fingerprint"]["sha256_canonical_json"]
        == AION200_EVALUATION_FINGERPRINT
    )

    binding = payload["pilot_binding"]
    assert binding["synthetic_environment_manifest"]["environment"] == (
        "local_offline_operator_evaluation"
    )
    assert binding["local_state_store_path"] == "/tmp/aion-os/aion-201/pilot-state.sqlite"
    assert binding["output_directory"] == "/tmp/aion-os/aion-201/redacted-pilot-evidence"
    assert len(binding["redacted_reference_set"]["references"]) == 10
    assert binding["operator_principal"] == (
        "operator-principal://aion-201/local-offline-evaluation-operator"
    )
    assert binding["expiry"] == (
        "AION-202 pilot evidence merge followed by AION-203 evaluation closeout"
    )

    budget = binding["run_budget"]
    assert budget == payload["resource_limits"]
    assert budget["maximum_sessions"] == 10
    assert budget["maximum_cycles_per_session"] == 100
    assert budget["maximum_total_cycles"] == 1000
    assert budget["maximum_wall_clock_seconds_per_session"] == 1800
    assert budget["maximum_concurrency"] == 2
    for key in (
        "network_calls",
        "source_mutations",
        "git_operations",
        "real_pull_requests",
        "approvals_created",
        "deployments",
        "production_exposure",
        "model_weight_changes",
    ):
        assert budget[key] == 0


def test_aion_201_ledgers_activate_single_non_reusable_pilot_authorization() -> None:
    validate_local_offline_pilot_authorization(ROOT)
    validate_local_offline_pilot_authorization_no_go(ROOT)

    program = _json("docs/cognitive-architecture/program-ledger.json")
    authorization = _json("docs/cognitive-architecture/authorization-ledger.json")
    aion202_executed = _aion202_evidence_exists()
    aion203_closed = _aion203_closeout_exists()
    expected_program_state = (
        AION203_PROGRAM_STATE
        if aion203_closed
        else AION202_PROGRAM_STATE
        if aion202_executed
        else AION201_PROGRAM_STATE
    )
    expected_implementation_state = (
        "aion_203_evaluation_passed_authorization_closed"
        if aion203_closed
        else "aion_202_pilot_executed_pending_aion_203_evaluation"
        if aion202_executed
        else "authorized_pending_aion_202_pilot_execution"
    )
    expected_active = None if aion203_closed else AION201_AUTHORIZATION_ID
    expected_count = 0 if aion203_closed else 1
    assert program["program_state"] == expected_program_state
    assert program["active_cognitive_implementation_authorization"] == expected_active
    assert (
        authorization["active_cognitive_implementation_authorization"]
        == expected_active
    )
    assert program["active_cognitive_implementation_authorization_count"] == expected_count
    assert authorization["active_cognitive_implementation_authorization_count"] == expected_count

    aion200 = next(
        record
        for record in program["records"]
        if record.get("task_id") == AION200_TASK_ID
        and record.get("evaluation_id") == AION200_EVALUATION_ID
    )
    assert aion200["task_state"] == "passed_recommended_aion_201_authorization_review"
    assert aion200["new_authorization_id"] is None
    assert aion200["authorized_task"] is None
    assert aion200["active_cognitive_implementation_authorization_count"] == 0

    program_record = next(
        record
        for record in program["records"]
        if record.get("authorization_id") == AION201_AUTHORIZATION_ID
    )
    auth_record = next(
        record
        for record in authorization["records"]
        if record.get("authorization_id") == AION201_AUTHORIZATION_ID
    )
    for record in (program_record, auth_record):
        assert record["task_id"] == AION201_TASK_ID
        assert record["authorization_active"] is (not aion203_closed)
        assert record["authorization_consumed"] is aion203_closed
        assert record["authorization_expired"] is aion203_closed
        assert record["authorization_reusable"] is False
        assert record["authorized_task"] == AION202_TASK_ID
        assert record["implementation_state"] == expected_implementation_state
        assert record["pilot_executed"] is aion202_executed
        if aion203_closed:
            assert record["authorization_closed_by_task"] == AION203_TASK_ID
            assert record["authorization_closeout_evaluation"] == AION203_EVALUATION_ID
            assert record["evaluation_result"] == "PASS"
        assert record["runtime_effect"] is False
        assert record["source_modified"] is False
        assert record["git_mutated"] is False
        assert record["pull_request_created"] is False
        assert record["approval_created"] is False
        assert record["merged"] is False
        assert record["production_exposure"] is False
        assert record["model_weights_changed"] is False


def test_aion_201_does_not_execute_pilot_or_enable_runtime_surface() -> None:
    program = _json("docs/cognitive-architecture/program-ledger.json")
    aion202_executed = _aion202_evidence_exists()
    has_aion202_execution_record = any(
        record.get("record_kind") == "implementation"
        and record.get("implementation_task") == AION202_TASK_ID
        for record in program["records"]
    )
    assert has_aion202_execution_record is aion202_executed
    assert not (ROOT / "services/brain-api/src/aion_brain/api/cognitive_runtime.py").exists()
    for relative in (
        "services/brain-api/src/aion_brain/kernel/container.py",
        "services/brain-api/src/aion_brain/kernel/diagnostics.py",
    ):
        text = (ROOT / relative).read_text()
        assert "ControlledCognitiveShadowRuntime" not in text
        assert "aion_brain.cognitive_runtime" not in text

    payload = _json(
        "examples/cognitive-architecture/aion-201-local-offline-pilot-authorization.json"
    )
    for key in (
        "pilot_executed",
        "source_modified_by_pilot",
        "git_mutated_by_pilot",
        "pull_request_created_by_pilot",
        "approval_created_by_pilot",
        "external_action_performed",
        "production_traffic_used",
    ):
        assert payload[key] is False


def test_aion_201_scripts_are_executable_and_pass() -> None:
    env = {
        **os.environ,
        "PYTEST_CURRENT_TEST": "AION-201 focused script test",
    }
    scripts = (
        "scripts/cognitive-local-offline-pilot-authorization-no-go-regression.sh",
        "scripts/cognitive-local-offline-pilot-authorization-check.sh",
    )
    for script in scripts:
        path = ROOT / script
        assert path.is_file()
        assert os.access(path, os.X_OK)
        subprocess.run([str(path)], cwd=ROOT, env=env, check=True)
