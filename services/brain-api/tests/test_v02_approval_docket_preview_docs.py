"""AION-141 v0.2 approval docket preview regression tests."""

from __future__ import annotations

import json
import os
import stat
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]

DOCS = [
    "docs/release/v02-approval-docket-preview.md",
    "docs/release/v02-runtime-approval-review-boundary.md",
    "docs/release/v02-implementation-decision-record-guard.md",
    "docs/release/v02-approval-docket-state-model.md",
    "docs/release/v02-approval-docket-evidence-pack.md",
    "docs/release/v02-approval-docket-no-go.md",
    "docs/release/v02-approval-docket-checklist.md",
    "docs/adr/0132-v02-approval-docket-preview.md",
]

EXAMPLES = [
    "examples/release/v02-approval-docket-preview.json",
    "examples/release/v02-runtime-approval-review-boundary.json",
    "examples/release/v02-implementation-decision-record-guard.json",
    "examples/release/v02-approval-docket-state-model.json",
    "examples/release/v02-approval-docket-evidence-pack.json",
    "operator-console-static/demo-data/v02-approval-docket-preview.json",
    "operator-console-static/demo-data/v02-implementation-decision-record-guard.json",
]

TRUE_KEYS = {
    "v02_approval_docket_preview_created",
    "approval_docket_preview_only",
    "implementation_decision_record_created",
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
    "approval_docket_item_approved",
    "implementation_decision_record_approval",
    "runtime_approval_review_approved",
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


def test_v02_approval_docket_preview_docs_exist_and_are_indexed() -> None:
    for relative in DOCS:
        assert (ROOT / relative).exists(), relative

    assert "0132-v02-approval-docket-preview.md" in _text("docs/adr/README.md")

    preview = _text("docs/release/v02-approval-docket-preview.md")
    for required in [
        "## Purpose",
        "## Scope",
        "## Approval Docket Is Preview-Only",
        "## Approval Docket Does Not Approve Implementation",
        "## Approval Docket Does Not Enable Runtime",
        "## Required Decision Package Fields",
        "## Required Decision Record Fields",
        "## Required Reviewer Evidence",
        "## Required ADR Dependency",
        "## Required Gate Dependency",
        "## Docket States",
        "AION-141 creates no v0.2 tag and no v0.2 release.",
    ]:
        assert required in preview

    boundary = _text("docs/release/v02-runtime-approval-review-boundary.md")
    for required in [
        "Runtime approval review is not runtime enablement",
        "Runtime approval review is not implementation approval",
        "Docket readiness is not implementation approval",
        "Decision record completeness is not runtime enablement",
        "Reviewer evidence is not implementation approval",
        "Review board routing is not implementation approval",
        "ADR dependency presence is not runtime enablement",
        "Gate dependency success is not runtime enablement",
        "runtime_approval_review_approved=false",
        "runtime_decision_lock_release_approved=false",
        "runtime_decision_readiness_approved=false",
        "runtime_implementation_approved=false",
        "decision_package_approval=false",
        "approval_docket_item_approved=false",
        "v02_release_approved=false",
    ]:
        assert required in boundary

    guard = _text("docs/release/v02-implementation-decision-record-guard.md")
    for required in [
        "implementation_decision_record_created=true",
        "implementation_decision_record_approval=false",
        "approval_docket_item_approved=false",
        "runtime_approval_review_approved=false",
        "runtime_decision_lock_release_approved=false",
        "runtime_decision_readiness_approved=false",
        "runtime_implementation_approved=false",
        "decision_package_approval=false",
        "approval_readiness_approved=false",
        "review_board_decision_approval=false",
        "routing_decision_approval=false",
        "reviewer_signoff_implementation_approval=false",
        "operator_write_execution_approved=false",
        "connector_implementation_approved=false",
        "production_auth_approved=false",
        "module_activation_approved=false",
        "external_calls_approved=false",
        "credential_storage_approved=false",
        "token_storage_approved=false",
        "sandbox_execution_approved=false",
        "v02_release_approved=false",
    ]:
        assert required in guard

    state_model = _text("docs/release/v02-approval-docket-state-model.md")
    for state in [
        "drafted",
        "docketed",
        "evidence_attached",
        "decision_record_attached",
        "review_ready_preview",
        "runtime_review_pending",
        "blocked",
        "rejected",
        "expired",
        "revoked",
        "docket_unapproved",
        "implementation_unapproved",
    ]:
        assert state in state_model
    assert "No state approves implementation or enables runtime." in state_model

    evidence = _text("docs/release/v02-approval-docket-evidence-pack.md")
    for required in [
        "decision package final review",
        "decision package stabilization",
        "approval readiness closeout",
        "runtime decision lock",
        "review board stabilization",
        "submission registry stabilization",
        "request pack final review",
        "planning track closeout",
        "final planning release gate",
        "docs and boundary checks",
        "Evidence source",
        "Required script",
        "Expected safe value",
        "Approval state",
        "Blocker",
        "Notes",
    ]:
        assert required in evidence

    no_go = _text("docs/release/v02-approval-docket-no-go.md")
    for condition in [
        "approval docket item approved true",
        "implementation decision record approval true",
        "runtime approval review approved true",
        "runtime decision lock release approved true",
        "runtime decision readiness approved true",
        "decision package approval true",
        "approval readiness approved true",
        "review board decision approval true",
        "routing decision approval true",
        "reviewer sign-off marked implementation approval true",
        "preapproval queue item approved true",
        "submission approval true",
        "request pack approval true",
        "request package implementation approved true",
        "proposal template implementation approved true",
        "approval evidence approval true",
        "evidence completeness bypassed",
        "submission freeze bypassed",
        "preapproval gate bypassed",
        "approval queue item approved true",
        "implementation approval true",
        "workstream implementation approval true",
        "proposal implementation approval true",
        "approval workflow bypassed",
        "approval record missing",
        "ADR dependency bypassed",
        "gate dependency bypassed",
        "v0.2 tag created",
        "v0.2 release created",
        "production auth enabled",
        "connector runtime enabled",
        "operator write execution enabled",
        "module activation enabled",
        "external calls enabled",
        "credential/token storage enabled",
        "sandbox execution enabled",
        "package files added",
        "migrations added",
        "runtime API execution routes added",
    ]:
        assert condition in no_go

    checklist = _text("docs/release/v02-approval-docket-checklist.md")
    for item in [
        "docs complete",
        "examples valid",
        "scripts executable",
        "decision package final review passing",
        "decision package stabilization passing",
        "review board stabilization passing",
        "submission registry stabilization passing",
        "request pack final review passing",
        "planning track closeout passing",
        "final planning release gate passing",
        "no approval docket item approval",
        "no implementation decision record approval",
        "no runtime approval review approval",
        "no runtime decision approval",
        "no decision package approval",
        "no approval readiness approval",
        "no review board approval",
        "no routing approval",
        "no runtime implementation",
        "no submission approval",
        "no preapproval queue approval",
        "no request approval",
        "no v0.2 tag",
        "no v0.2 release",
        "no external calls",
        "no credentials/tokens",
        "no sandbox execution",
        "no package files",
        "no migrations",
    ]:
        assert item in checklist

    adr = _text("docs/adr/0132-v02-approval-docket-preview.md")
    for required in [
        "Decision: add v0.2 approval docket preview.",
        "Decision: AION-141 does not approve implementation.",
        "Decision: approval dockets and implementation decision records remain preview-only.",
        "Decision: approval docket item approval remains false.",
        "Decision: implementation decision record approval remains false.",
        "Decision: runtime approval review approval remains false.",
        (
            "Decision: future implementation still requires explicit approval records, "
            "ADRs, and gate evidence."
        ),
        "Decision: no v0.2 release or tag is created.",
        (
            "Reason: AION needs an approval docket boundary before runtime "
            "decisions can be considered."
        ),
        (
            "Consequence: future implementation candidates remain blocked until docketed "
            "evidence and explicit approval records exist."
        ),
        "Constraint: no runtime enablement.",
        "Constraint: no external calls.",
        "Constraint: no credentials/tokens.",
        "Constraint: no sandbox execution.",
        "Constraint: no privileged bypass.",
    ]:
        assert required in adr


def test_v02_approval_docket_preview_examples_are_safe() -> None:
    for relative in EXAMPLES:
        payload = _json(relative)
        assert payload["task_id"] == "AION-141"
        assert payload["status"] == "passed"
        assert payload["synthetic"] is True
        assert CONTENT_SAFETY.issubset(set(payload["content_safety"]))
        for key in TRUE_KEYS:
            assert payload[key] is True, f"{relative}.{key} must be true"
        _assert_false_keys(payload, relative)

    state_model = _json("examples/release/v02-approval-docket-state-model.json")
    assert len(state_model["states"]) == 12
    for row in state_model["states"]:
        assert row["implementation_approval"] is False
        assert row["runtime_enabled"] is False

    evidence = _json("examples/release/v02-approval-docket-evidence-pack.json")
    assert len(evidence["evidence_rows"]) >= 10
    for row in evidence["evidence_rows"]:
        assert row["approval_state"] is False
        assert (
            row["approval_marker"].endswith("=false")
            or row["approval_marker"] == "no approval granted"
        )

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


def test_v02_approval_docket_preview_scripts_are_executable_and_pass() -> None:
    scripts = [
        ROOT / "scripts/v02-approval-docket-preview-check.sh",
        ROOT / "scripts/v02-runtime-approval-review-freeze.sh",
        ROOT / "scripts/v02-approval-docket-no-go-regression.sh",
    ]
    for script in scripts:
        assert script.exists(), script
        assert script.stat().st_mode & stat.S_IXUSR, script
        subprocess.run(["bash", "-n", str(script)], cwd=ROOT, check=True)

    env = {
        **os.environ,
        "AION_V02_APPROVAL_DOCKET_PREVIEW_SKIP_INHERITED_GATES": "1",
        "AION_V02_RUNTIME_APPROVAL_REVIEW_FREEZE_SKIP_FULL_CHECK": "1",
        "AION_V02_DECISION_PACKAGE_FINAL_REVIEW_SKIP_INHERITED_GATES": "1",
        "AION_V02_RUNTIME_DECISION_LOCK_FREEZE_SKIP_FULL_CHECK": "1",
    }
    for command in [
        "./scripts/v02-approval-docket-preview-check.sh",
        "./scripts/v02-runtime-approval-review-freeze.sh",
        "./scripts/v02-approval-docket-no-go-regression.sh",
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
