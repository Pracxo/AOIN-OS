"""AION-142 v0.2 approval docket stabilization regression tests."""

from __future__ import annotations

import json
import os
import stat
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]

DOCS = [
    "docs/release/v02-approval-docket-stabilization-gate.md",
    "docs/release/v02-implementation-decision-record-freeze.md",
    "docs/release/v02-runtime-approval-review-evidence-baseline.md",
    "docs/release/v02-approval-docket-lifecycle-evidence-matrix.md",
    "docs/release/v02-approval-docket-stabilization-summary.md",
    "docs/release/v02-approval-docket-stabilization-no-go.md",
    "docs/release/v02-approval-docket-closeout-checklist.md",
    "docs/adr/0133-v02-approval-docket-stabilization.md",
]

EXAMPLES = [
    "examples/release/v02-approval-docket-stabilization-gate.json",
    "examples/release/v02-implementation-decision-record-freeze.json",
    "examples/release/v02-runtime-approval-review-evidence-baseline.json",
    "examples/release/v02-approval-docket-lifecycle-evidence-matrix.json",
    "examples/release/v02-approval-docket-stabilization-summary.json",
    "operator-console-static/demo-data/v02-approval-docket-stabilization.json",
    "operator-console-static/demo-data/v02-implementation-decision-record-freeze.json",
]

TRUE_KEYS = {
    "v02_approval_docket_stabilized",
    "v02_approval_docket_preview_created",
    "approval_docket_preview_only",
    "implementation_decision_record_created",
    "implementation_decision_record_freeze_created",
    "runtime_approval_review_evidence_baseline_created",
    "approval_docket_lifecycle_matrix_created",
    "decision_package_preview_only",
    "approval_readiness_preview_only",
    "runtime_decision_lock_created",
    "review_board_planning_only",
    "submission_registry_preview_only",
    "preapproval_queue_preview_only",
    "proposal_registry_preview_only",
    "approval_queue_preview_only",
}

FALSE_KEYS = {
    "approval_docket_stabilization_approval",
    "approval_docket_item_approved",
    "implementation_decision_record_approval",
    "implementation_decision_record_freeze_approval",
    "runtime_approval_review_approved",
    "runtime_approval_review_evidence_approved",
    "decision_package_approval",
    "approval_readiness_approved",
    "runtime_decision_lock_release_approved",
    "runtime_decision_readiness_approved",
    "review_board_decision_approval",
    "routing_decision_approval",
    "reviewer_signoff_implementation_approval",
    "preapproval_queue_item_approved",
    "request_pack_approval",
    "submission_approval",
    "v02_tag_created",
    "v02_release_created",
    "v02_release_approved",
    "runtime_implementation_approved",
    "backlog_implementation_items_approved",
    "workstream_implementation_approved",
    "proposal_implementation_approved",
    "approval_queue_item_approved",
    "approval_workflow_bypassed",
    "approval_record_missing",
    "adr_dependency_bypassed",
    "gate_dependency_bypassed",
    "evidence_completeness_bypassed",
    "submission_freeze_bypassed",
    "preapproval_gate_bypassed",
    "operator_write_execution_approved",
    "connector_implementation_approved",
    "production_auth_approved",
    "module_activation_approved",
    "external_calls_approved",
    "credential_storage_approved",
    "token_storage_approved",
    "sandbox_execution_approved",
    "api_runtime_execution_route_added",
    "sdk_resource_implementation_added",
    "cli_command_implementation_added",
    "package_files_added",
    "migrations_added",
    "secrets_present",
    "tokens_present",
    "credentials_present",
    "endpoints_present",
    "prompt_payloads_present",
    "private_reasoning_present",
}

FORBIDDEN_ACTIONS = {
    "activate_module",
    "activate_capability",
    "load_code",
    "execute_tool",
    "enable_external_model_calls",
    "hard_delete",
}

CONTENT_SAFETY = {
    "no secrets",
    "no tokens",
    "no credentials",
    "no endpoints",
    "no raw prompts",
    "no hidden reasoning",
}


def test_v02_approval_docket_stabilization_docs_exist_and_are_indexed() -> None:
    for relative in DOCS:
        assert (ROOT / relative).exists(), relative

    assert "0133-v02-approval-docket-stabilization.md" in _text("docs/adr/README.md")

    gate = _text("docs/release/v02-approval-docket-stabilization-gate.md")
    for required in [
        "## Purpose",
        "## Scope",
        "## Stabilization Values",
        "## Required Gate Stack",
        "## Required Artifacts",
        "## Stabilization Is Not Approval",
        "## Runtime Boundary",
        "AION-142 creates no v0.2 tag and no v0.2 release.",
        "v02_approval_docket_stabilized=true",
        "approval_docket_stabilization_approval=false",
        "implementation_decision_record_freeze_approval=false",
        "runtime_approval_review_approved=false",
        "runtime_implementation_approved=false",
    ]:
        assert required in gate

    freeze = _text("docs/release/v02-implementation-decision-record-freeze.md")
    for required in [
        "implementation_decision_record_freeze_created=true",
        "implementation_decision_record_freeze_approval=false",
        "approval_docket_stabilization_approval=false",
        "runtime_approval_review_evidence_approved=false",
        "runtime_implementation_approved=false",
        "Frozen implementation decision records are not approval records.",
    ]:
        assert required in freeze

    baseline = _text("docs/release/v02-runtime-approval-review-evidence-baseline.md")
    for required in [
        "approval docket stabilization",
        "implementation decision record freeze",
        "runtime approval review boundary",
        "runtime decision lock",
        "decision package final review",
        "review board stabilization",
        "submission registry stabilization",
        "request pack final review",
        "final planning release gate",
        "Runtime approval review evidence is not runtime approval.",
    ]:
        assert required in baseline

    matrix = _text("docs/release/v02-approval-docket-lifecycle-evidence-matrix.md")
    for state in [
        "drafted",
        "docketed",
        "evidence_attached",
        "decision_record_attached",
        "review_ready_preview",
        "runtime_review_pending",
        "stabilization_frozen",
        "record_freeze_created",
        "blocked",
        "rejected",
        "expired",
        "revoked",
        "docket_unapproved",
        "implementation_unapproved",
    ]:
        assert state in matrix
    assert "No lifecycle state approves implementation or enables runtime." in matrix

    no_go = _text("docs/release/v02-approval-docket-stabilization-no-go.md")
    for condition in [
        "approval docket stabilization approval true",
        "approval docket item approved true",
        "implementation decision record freeze approval true",
        "implementation decision record approval true",
        "runtime approval review evidence approved true",
        "runtime approval review approved true",
        "runtime decision lock release approved true",
        "runtime decision readiness approved true",
        "decision package approval true",
        "approval readiness approved true",
        "review board decision approval true",
        "routing decision approval true",
        "reviewer sign-off marked implementation approval true",
        "v0.2 tag created",
        "v0.2 release created",
        "runtime API execution routes added",
        "SDK resource implementation added",
        "CLI command implementation added",
    ]:
        assert condition in no_go

    checklist = _text("docs/release/v02-approval-docket-closeout-checklist.md")
    for item in [
        "approval docket stabilization gate passing",
        "implementation decision record freeze passing",
        "approval docket stabilization no-go regression passing",
        "no approval docket stabilization approval",
        "no implementation decision record freeze approval",
        "no runtime approval review approval",
        "no runtime implementation",
        "no v0.2 tag",
        "no v0.2 release",
        "no SDK resource implementation",
        "no CLI command implementation",
    ]:
        assert item in checklist

    adr = _text("docs/adr/0133-v02-approval-docket-stabilization.md")
    for required in [
        "Decision: add v0.2 approval docket stabilization.",
        "Decision: freeze implementation decision records as unapproved planning records.",
        "Decision: add runtime approval review evidence baseline.",
        "Decision: add approval docket lifecycle evidence matrix.",
        "Decision: AION-142 does not approve implementation.",
        "Decision: approval docket stabilization approval remains false.",
        "Decision: implementation decision record freeze approval remains false.",
        "Decision: no v0.2 release or tag is created.",
        "Constraint: no runtime enablement.",
        "Constraint: no external calls.",
        "Constraint: no credentials/tokens.",
        "Constraint: no sandbox execution.",
        "Constraint: no package or migration changes.",
        "Constraint: no API, SDK, or CLI implementation changes.",
        "Constraint: no privileged bypass.",
    ]:
        assert required in adr


def test_v02_approval_docket_stabilization_examples_are_safe() -> None:
    for relative in EXAMPLES:
        payload = _json(relative)
        assert payload["task_id"] == "AION-142"
        assert payload["status"] == "passed"
        assert payload["synthetic"] is True
        assert CONTENT_SAFETY.issubset(set(payload["content_safety"]))
        for key in TRUE_KEYS:
            assert payload[key] is True, f"{relative}.{key} must be true"
        _assert_false_keys(payload, relative)

    baseline = _json("examples/release/v02-runtime-approval-review-evidence-baseline.json")
    assert len(baseline["evidence_rows"]) >= 5
    for row in baseline["evidence_rows"]:
        assert row["approval_state"] is False
        assert row["approval_marker"].endswith("=false")

    matrix = _json("examples/release/v02-approval-docket-lifecycle-evidence-matrix.json")
    assert len(matrix["states"]) >= 14
    for row in matrix["states"]:
        assert row["approval_state"] is False
        assert row["runtime_enabled"] is False
        assert row["blocker"]

    for relative in EXAMPLES[-2:]:
        payload = _json(relative)
        assert payload["read_only"] is True
        assert payload["redaction_applied"] is True
        assert payload["sections"]
        assert payload["blockers"]
        assert payload["warnings"]
        assert payload["refs"]
        assert payload["forbidden_actions"]
        action_keys = {action["action_key"] for action in payload["forbidden_actions"]}
        assert action_keys == FORBIDDEN_ACTIONS
        for action in payload["forbidden_actions"]:
            assert action["allowed"] is False


def test_v02_approval_docket_stabilization_scripts_are_executable_and_pass() -> None:
    scripts = [
        ROOT / "scripts/v02-approval-docket-stabilization-gate.sh",
        ROOT / "scripts/v02-implementation-decision-record-freeze.sh",
        ROOT / "scripts/v02-approval-docket-stabilization-no-go-regression.sh",
    ]
    for script in scripts:
        assert script.exists(), script
        assert script.stat().st_mode & stat.S_IXUSR, script
        subprocess.run(["bash", "-n", str(script)], cwd=ROOT, check=True)

    env = {
        **os.environ,
        "AION_V02_APPROVAL_DOCKET_STABILIZATION_SKIP_INHERITED_GATES": "1",
        "AION_V02_IMPLEMENTATION_DECISION_RECORD_FREEZE_SKIP_FULL_CHECK": "1",
        "AION_V02_APPROVAL_DOCKET_PREVIEW_SKIP_INHERITED_GATES": "1",
        "AION_V02_RUNTIME_APPROVAL_REVIEW_FREEZE_SKIP_FULL_CHECK": "1",
        "AION_V02_DECISION_PACKAGE_FINAL_REVIEW_SKIP_INHERITED_GATES": "1",
        "AION_V02_RUNTIME_DECISION_LOCK_FREEZE_SKIP_FULL_CHECK": "1",
    }
    for command in [
        "./scripts/v02-approval-docket-stabilization-gate.sh",
        "./scripts/v02-implementation-decision-record-freeze.sh",
        "./scripts/v02-approval-docket-stabilization-no-go-regression.sh",
    ]:
        subprocess.run([command], cwd=ROOT, check=True, env=env)


def _text(relative: str) -> str:
    return (ROOT / relative).read_text()


def _json(relative: str) -> dict[str, Any]:
    return json.loads((ROOT / relative).read_text())


def _assert_false_keys(value: Any, context: str) -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            if key in FALSE_KEYS:
                assert nested is False, f"{context}.{key} must be false"
            if key in {
                "implementation_approval",
                "implementation_approved",
                "submission_approved",
                "runtime_enabled",
                "approval_state",
                "implementation_state",
                "release_approval",
                "approval_record_created",
            }:
                assert nested is False, f"{context}.{key} must be false"
            _assert_false_keys(nested, f"{context}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _assert_false_keys(item, f"{context}[{index}]")
