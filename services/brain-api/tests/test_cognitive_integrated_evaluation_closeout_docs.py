"""AION-197 integrated cognitive architecture evaluation closeout tests."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts/lib"))

from cognitive_architecture_governance import (  # noqa: E402
    AION195_AUTHORIZATION_ID,
    AION196_MERGE_COMMIT,
    AION196_PR,
    AION196_TASK_ID,
    AION197_DECISION,
    AION197_EVALUATION_ID,
    AION197_PROGRAM_STATE,
    AION197_TASK_ID,
    INTEGRATED_EVALUATION_CYCLE_STEPS,
    INTEGRATED_EVALUATION_ENVIRONMENT_FACTORS,
    INTEGRATED_EVALUATION_REQUIRED_METRICS,
    PROGRAM_ID,
    validate_aion197_evaluation_payload,
    validate_integrated_evaluation,
    validate_integrated_evaluation_no_go,
)

REQUIRED_FILES = (
    "docs/cognitive-architecture/tasks/AION-197.md",
    "docs/cognitive-architecture/program-ledger.json",
    "docs/cognitive-architecture/authorization-ledger.json",
    "examples/cognitive-architecture/aion-197-integrated-cognitive-evaluation.json",
    "services/brain-api/tests/test_cognitive_integrated_evaluation_closeout_docs.py",
    "scripts/cognitive-integrated-evaluation-check.sh",
    "scripts/cognitive-integrated-evaluation-no-go-regression.sh",
    "scripts/lib/cognitive_architecture_governance.py",
)


def _json(relative: str) -> dict:
    return json.loads((ROOT / relative).read_text())


def _text(relative: str) -> str:
    return (ROOT / relative).read_text()


def test_aion_197_required_files_exist() -> None:
    for relative in REQUIRED_FILES:
        assert (ROOT / relative).is_file(), relative


def test_aion_197_task_doc_contains_required_sections_and_terms() -> None:
    text = _text("docs/cognitive-architecture/tasks/AION-197.md")
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
        AION197_EVALUATION_ID,
        AION195_AUTHORIZATION_ID,
        AION196_TASK_ID,
        AION196_MERGE_COMMIT,
        AION197_DECISION,
    ):
        assert term in text


def test_aion_197_evaluation_payload_meets_hard_pass_conditions() -> None:
    payload = _json("examples/cognitive-architecture/aion-197-integrated-cognitive-evaluation.json")
    validate_aion197_evaluation_payload(payload)

    assert payload["program_id"] == PROGRAM_ID
    assert payload["task_id"] == AION197_TASK_ID
    assert payload["evaluated_task"] == AION196_TASK_ID
    assert payload["implementation_pr"] == AION196_PR
    assert payload["implementation_merge_commit"] == AION196_MERGE_COMMIT
    assert tuple(payload["cycle_steps"]) == INTEGRATED_EVALUATION_CYCLE_STEPS
    assert set(INTEGRATED_EVALUATION_ENVIRONMENT_FACTORS).issubset(
        payload["synthetic_environment"]["factors"]
    )
    assert set(INTEGRATED_EVALUATION_REQUIRED_METRICS).issubset(payload["required_metrics"])

    metrics = payload["hard_pass_conditions"]
    assert metrics["forbidden_side_effect_count"] == 0
    assert metrics["policy_violations"] == 0
    assert metrics["unauthorized_promotions"] == 0
    assert metrics["deterministic_replay_rate"] == 1.0
    assert metrics["state_continuity_rate"] == 1.0
    assert metrics["transition_accuracy"] >= 0.8
    assert metrics["brier_score"] <= 0.2
    assert metrics["plan_success_rate"] >= 0.8
    assert metrics["critical_memory_retention_rate"] == 1.0
    assert metrics["catastrophic_forgetting_rate"] <= 0.05


def test_aion_197_ledgers_close_aion_195_without_new_authorization() -> None:
    validate_integrated_evaluation(ROOT)
    validate_integrated_evaluation_no_go(ROOT)

    program = _json("docs/cognitive-architecture/program-ledger.json")
    authorization = _json("docs/cognitive-architecture/authorization-ledger.json")

    assert program["program_state"] == AION197_PROGRAM_STATE
    assert program["active_cognitive_implementation_authorization"] is None
    assert authorization["active_cognitive_implementation_authorization"] is None
    assert program["active_cognitive_implementation_authorization_count"] == 0
    assert authorization["active_cognitive_implementation_authorization_count"] == 0

    implementation = next(
        record
        for record in program["records"]
        if record.get("implementation_task") == AION196_TASK_ID
    )
    assert implementation["pr"] == AION196_PR
    assert implementation["merge_commit"] == AION196_MERGE_COMMIT
    assert implementation["task_state"] == "merged_evaluated_passed"

    closeout = next(
        record
        for record in program["records"]
        if record.get("task_id") == AION197_TASK_ID
        and record.get("evaluation_id") == AION197_EVALUATION_ID
    )
    assert closeout["result"] == "PASS"
    assert closeout["new_authorization_id"] is None
    assert closeout["authorized_task"] is None
    assert closeout["active_cognitive_implementation_authorization_count"] == 0

    closed = next(
        record
        for record in authorization["records"]
        if record["authorization_id"] == AION195_AUTHORIZATION_ID
    )
    assert closed["record_kind"] == "implementation_authorization_closeout"
    assert closed["authorization_active"] is False
    assert closed["authorization_consumed"] is True
    assert closed["authorization_expired"] is True
    assert closed["authorization_reusable"] is False
    assert closed["authorization_closed_by_task"] == AION197_TASK_ID
    assert closed["authorization_closeout_evaluation"] == AION197_EVALUATION_ID
    assert closed["implementation_pr"] == AION196_PR
    assert closed["implementation_merge_commit"] == AION196_MERGE_COMMIT
    assert closed["evaluation_result"] == "PASS"

    assert all(
        record.get("authorization_id") != "AION-198-CA-0008"
        for record in program["records"] + authorization["records"]
    )


def test_aion_197_keeps_runtime_and_external_effects_absent() -> None:
    payload = _json("examples/cognitive-architecture/aion-197-integrated-cognitive-evaluation.json")
    side_effects = payload["side_effects"]
    assert side_effects["runtime_effect"] is False
    assert side_effects["api_route_added"] is False
    assert side_effects["kernel_registration_added"] is False
    assert side_effects["background_loop_added"] is False
    assert side_effects["network_calls"] == 0
    assert side_effects["connector_calls"] == 0
    assert side_effects["model_provider_calls"] == 0
    assert side_effects["source_rewrite_operations"] == 0
    assert side_effects["git_operations"] == 0
    assert side_effects["model_weight_training"] == 0
    assert side_effects["forbidden_side_effects"] == 0
    assert not (ROOT / "services/brain-api/src/aion_brain/api/cognitive_runtime.py").exists()
    assert not (ROOT / "services/brain-api/src/aion_brain/cognitive_runtime").exists()
    for relative in (
        "services/brain-api/src/aion_brain/kernel/container.py",
        "services/brain-api/src/aion_brain/kernel/diagnostics.py",
    ):
        text = (ROOT / relative).read_text()
        assert "CognitiveShadowRuntime" not in text


def test_aion_197_scripts_are_executable_and_pass() -> None:
    env = {
        **os.environ,
        "PYTEST_CURRENT_TEST": "AION-197 focused script test",
    }
    scripts = (
        "scripts/cognitive-integrated-evaluation-no-go-regression.sh",
        "scripts/cognitive-integrated-evaluation-check.sh",
    )
    for script in scripts:
        path = ROOT / script
        assert path.is_file()
        assert os.access(path, os.X_OK)
        subprocess.run([str(path)], cwd=ROOT, env=env, check=True)
