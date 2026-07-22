"""AION-180 shadow activation authorization documentation tests."""

from __future__ import annotations

import json
import os
import stat
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts/lib"))

from self_improvement_governance import (  # noqa: E402
    AION180_REQUIRED_DOCS,
    AION180_REQUIRED_EXAMPLES,
    AION_179_FEATURE_COMMITS,
    AION_179_MERGE_COMMIT,
    AION_179_MERGED_AT,
    SHADOW_ACTIVATION_AUTHORIZATION_ID,
    SHADOW_ACTIVATION_CLOSEOUT_TASK,
    SHADOW_ACTIVATION_IMPLEMENTATION_TASK,
    SHADOW_ACTIVATION_PROGRAM_ID,
    SHADOW_ACTIVATION_SCOPE,
    SHADOW_OPERATOR_EVALUATION_DECISION,
    SHADOW_OPERATOR_EVALUATION_ID,
    validate_shadow_activation_authorization_example,
)


def test_aion180_required_artifacts_exist_and_are_indexed() -> None:
    for relative in (*AION180_REQUIRED_DOCS, *AION180_REQUIRED_EXAMPLES):
        assert (ROOT / relative).is_file(), relative

    adr_index = _text("docs/adr/README.md")
    assert "0165-controlled-shadow-activation-control-plane-authorization.md" in adr_index


def test_aion179_delivery_verification_is_exact() -> None:
    ledger = _json("docs/self-improvement/program-ledger.json")
    by_task = {record["task_id"]: record for record in ledger["records"]}
    aion179 = by_task["AION-179"]

    assert aion179["branch"] == "phase/self-improvement-shadow-mode-evaluation-closeout"
    assert tuple(aion179["feature_commits"]) == AION_179_FEATURE_COMMITS
    assert aion179["pull_requests"] == [90]
    assert aion179["merge_commits"] == [AION_179_MERGE_COMMIT]
    assert aion179["ci_result"] == "pass"
    assert aion179["completion_timestamp"] == AION_179_MERGED_AT

    report = _json("examples/self-improvement/shadow-mode-operator-evaluation-report.json")
    assert report["evaluation_id"] == SHADOW_OPERATOR_EVALUATION_ID
    assert report["evaluation_type"] == "read_only_shadow_mode_operator_evaluation"
    assert report["decision"] == SHADOW_OPERATOR_EVALUATION_DECISION
    assert report["evaluation_passed"] is True
    assert report["scenario_count"] == 14
    assert all(item["passed"] for item in report["scenario_results"])
    assert all(report["hard_gates"].values())
    assert all(value is False for value in report["output_state"].values())


def test_aion180_authorization_example_matches_canonical_contract() -> None:
    payload = _json("examples/self-improvement/shadow-activation-authorization.json")
    validate_shadow_activation_authorization_example(payload)
    assert payload["activation_program_id"] == SHADOW_ACTIVATION_PROGRAM_ID
    assert payload["authorization_transaction_id"] == SHADOW_ACTIVATION_AUTHORIZATION_ID
    assert payload["approval_record_id"] == SHADOW_ACTIVATION_AUTHORIZATION_ID
    assert payload["implementation_task"] == SHADOW_ACTIVATION_IMPLEMENTATION_TASK
    assert payload["formal_closeout_task"] == SHADOW_ACTIVATION_CLOSEOUT_TASK
    assert payload["authorization_scope"] == SHADOW_ACTIVATION_SCOPE
    assert payload["shadow_activation_control_plane_authorized"] is True
    assert payload["shadow_activation_control_plane_implemented"] is False
    assert payload["shadow_activation_enabled"] is False


def test_aion180_scripts_are_executable() -> None:
    for relative in (
        "scripts/self-improvement-shadow-activation-authorization-no-go-regression.sh",
        "scripts/self-improvement-shadow-activation-authorization-check.sh",
        "scripts/self-improvement-shadow-activation-runtime-hold.sh",
    ):
        assert os.stat(ROOT / relative).st_mode & stat.S_IXUSR, relative


def test_project_status_reports_aion180_current_state() -> None:
    text = _text("docs/project-status.md")
    current = text.split("## Historical Compatibility Markers", 1)[0]
    historical = text.split("## Historical Compatibility Markers", 1)[1]
    assert "AION-204 Cognitive Architecture closeout reconciliation" in current
    assert "Knowledge Intelligence research plane authorized and not implemented" in current
    assert "active self-improvement implementation authorization count is zero" in current
    assert "`knowledge_research_runtime_enabled=false`" in current
    assert "`active_knowledge_implementation_task=AION-205`" in current
    assert "AION-180-SI-0007" in historical
    assert "AION-182 later closed AION-180-SI-0007" in historical


def _json(relative: str) -> dict[str, Any]:
    with (ROOT / relative).open() as handle:
        payload = json.load(handle)
    assert isinstance(payload, dict)
    return payload


def _text(relative: str) -> str:
    return (ROOT / relative).read_text()
