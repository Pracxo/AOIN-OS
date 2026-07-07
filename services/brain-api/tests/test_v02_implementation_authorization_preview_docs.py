"""AION-147 v0.2 implementation authorization preview regression tests."""

from __future__ import annotations

import json
import os
import stat
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]

DOCS = [
    "docs/release/v02-implementation-authorization-preview.md",
    "docs/release/v02-explicit-approval-record-schema.md",
    "docs/release/v02-runtime-enablement-guard-boundary.md",
    "docs/release/v02-authorization-state-model.md",
    "docs/release/v02-authorization-evidence-matrix.md",
    "docs/release/v02-implementation-authorization-no-go.md",
    "docs/release/v02-implementation-authorization-checklist.md",
    "docs/adr/0138-v02-implementation-authorization-preview.md",
]

EXAMPLES = [
    "examples/release/v02-implementation-authorization-preview.json",
    "examples/release/v02-explicit-approval-record-schema.json",
    "examples/release/v02-runtime-enablement-guard-boundary.json",
    "examples/release/v02-authorization-state-model.json",
    "examples/release/v02-authorization-evidence-matrix.json",
    "operator-console-static/demo-data/v02-implementation-authorization-preview.json",
    "operator-console-static/demo-data/v02-runtime-enablement-guard-boundary.json",
]

SCRIPTS = [
    "scripts/v02-implementation-authorization-preview-check.sh",
    "scripts/v02-runtime-enablement-guard-freeze.sh",
    "scripts/v02-implementation-authorization-no-go-regression.sh",
]

TRUE_KEYS = {
    "v02_implementation_authorization_preview_created",
    "implementation_authorization_preview_only",
    "explicit_approval_record_created",
    "runtime_enablement_guard_created",
    "runtime_approval_board_preview_only",
    "approval_vote_record_created",
    "go_no_go_ledger_created",
    "implementation_no_go_status",
    "approval_docket_preview_only",
    "implementation_decision_record_created",
    "runtime_approval_lock_created",
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
    "implementation_authorization_approved",
    "explicit_approval_record_approval",
    "runtime_enablement_guard_release_approved",
    "runtime_approval_board_decision_approved",
    "runtime_approval_board_final_review_approval",
    "approval_vote_record_approval",
    "approval_vote_record_closeout_approval",
    "approval_vote_record_runtime_effect",
    "implementation_go_status",
    "implementation_go_final_approval",
    "go_no_go_ledger_runtime_effect",
    "approval_docket_item_approved",
    "approval_docket_final_review_approval",
    "implementation_decision_record_approval",
    "implementation_decision_record_closeout_approval",
    "runtime_approval_lock_release_approved",
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
    "approval_status",
    "implementation_authorization_status",
    "runtime_guard_release_status",
    "secrets_present",
    "tokens_present",
    "credentials_present",
    "endpoints_present",
    "prompt_payloads_present",
    "private_reasoning_present",
}

CONTENT_SAFETY = {
    "no secrets",
    "no tokens",
    "no credentials",
    "no endpoints",
    "no raw prompts",
    "no hidden reasoning",
}

FORBIDDEN_ACTIONS = {
    "activate_module",
    "activate_capability",
    "load_code",
    "execute_tool",
    "enable_external_model_calls",
    "hard_delete",
}


def test_v02_implementation_authorization_docs_exist_and_are_indexed() -> None:
    for relative in DOCS:
        assert (ROOT / relative).exists(), relative

    assert "0138-v02-implementation-authorization-preview.md" in _text(
        "docs/adr/README.md"
    )

    preview = _text("docs/release/v02-implementation-authorization-preview.md")
    for required in [
        "## Purpose",
        "## Scope",
        "## Required Prior Gates",
        "## Authorization Preview Is Planning-Only",
        "## Authorization Preview Does Not Approve Implementation",
        "## Authorization Preview Does Not Enable Runtime",
        "## Required Explicit Approval Record Fields",
        "## Required Runtime Guard Fields",
        "## Required Implementation Go/No-Go Ledger Evidence",
        "## Required Vote Record Evidence",
        "## Required ADR Dependency",
        "## Required Gate Dependency",
        "AION-147 creates no v0.2 tag and no v0.2 release.",
        "implementation_authorization_preview_only=true",
        "implementation_authorization_approved=false",
        "explicit_approval_record_approval=false",
        "runtime_enablement_guard_release_approved=false",
        "runtime_implementation_approved=false",
    ]:
        assert required in preview

    schema = _text("docs/release/v02-explicit-approval-record-schema.md")
    for required in [
        "approval_record_id",
        "candidate_id",
        "workstream",
        "requested_runtime_capability",
        "approval_status",
        "implementation_authorization_status",
        "runtime_guard_release_status",
        "approved_by",
        "reviewers",
        "required_adr",
        "required_gate",
        "evidence_refs",
        "security_review_refs",
        "architecture_review_refs",
        "operator_review_refs",
        "rollback_plan_ref",
        "audit_provenance_ref",
        "expiry",
        "revocation_path",
        "no_go_acknowledgement",
        "created_at",
        "metadata",
        "approval_status=false",
        "implementation_authorization_status=false",
        "runtime_guard_release_status=false",
    ]:
        assert required in schema

    guard = _text("docs/release/v02-runtime-enablement-guard-boundary.md")
    for required in [
        "runtime_enablement_guard_created=true",
        "runtime_enablement_guard_release_approved=false",
        "implementation_authorization_approved=false",
        "explicit_approval_record_approval=false",
        "runtime_approval_board_decision_approved=false",
        "approval_vote_record_approval=false",
        "implementation_go_status=false",
        "implementation_no_go_status=true",
        "runtime_approval_lock_release_approved=false",
        "runtime_approval_review_approved=false",
        "runtime_implementation_approved=false",
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

    state_model = _text("docs/release/v02-authorization-state-model.md")
    for required in [
        "drafted",
        "approval_record_drafted",
        "evidence_attached",
        "guard_bound",
        "authorization_review_preview",
        "authorization_pending",
        "authorization_blocked",
        "rejected",
        "expired",
        "revoked",
        "authorization_unapproved",
        "implementation_unapproved",
        "No state in this model approves implementation or enables runtime.",
    ]:
        assert required in state_model

    matrix = _text("docs/release/v02-authorization-evidence-matrix.md")
    for required in [
        "Authorization area",
        "Required evidence",
        "Required reviewer",
        "Required ADR",
        "Required gate",
        "Approval record state",
        "Authorization state",
        "Runtime guard release state",
        "Runtime enabled",
        "Release blocker if violated",
        "Notes",
    ]:
        assert required in matrix


def test_v02_implementation_authorization_examples_are_locked() -> None:
    for relative in EXAMPLES:
        payload = _json(relative)
        for key in TRUE_KEYS:
            assert payload.get(key) is True, f"{relative}: {key}"
        for key in FALSE_KEYS:
            assert payload.get(key) is False, f"{relative}: {key}"
        assert CONTENT_SAFETY.issubset(set(payload.get("content_safety", [])))
        actions = {
            action.get("action_key")
            for action in payload.get("forbidden_actions", [])
            if isinstance(action, dict) and action.get("allowed") is False
        }
        assert FORBIDDEN_ACTIONS.issubset(actions)
        _assert_nested_false(payload)


def test_v02_implementation_authorization_scripts_exist_and_pass() -> None:
    env = os.environ.copy()
    env["AION_V02_IMPLEMENTATION_AUTHORIZATION_PREVIEW_SKIP_INHERITED_GATES"] = "1"
    env["AION_V02_RUNTIME_ENABLEMENT_GUARD_SKIP_FULL_CHECK"] = "1"

    for relative in SCRIPTS:
        script = ROOT / relative
        assert script.exists(), relative
        assert os.access(script, os.X_OK), relative
        assert script.stat().st_mode & stat.S_IXUSR, relative

    expected = [
        (
            "scripts/v02-implementation-authorization-preview-check.sh",
            "v0.2 implementation authorization preview check PASS",
        ),
        (
            "scripts/v02-runtime-enablement-guard-freeze.sh",
            "v0.2 runtime enablement guard freeze PASS",
        ),
        (
            "scripts/v02-implementation-authorization-no-go-regression.sh",
            "v0.2 implementation authorization no-go regression PASS",
        ),
    ]
    for relative, marker in expected:
        result = subprocess.run(
            [str(ROOT / relative)],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
            env=env,
        )
        assert marker in result.stdout


def _text(relative: str) -> str:
    return (ROOT / relative).read_text()


def _json(relative: str) -> dict[str, Any]:
    return json.loads((ROOT / relative).read_text())


def _assert_nested_false(value: Any) -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            if key in FALSE_KEYS:
                assert nested is False, key
            _assert_nested_false(nested)
    elif isinstance(value, list):
        for nested in value:
            _assert_nested_false(nested)
