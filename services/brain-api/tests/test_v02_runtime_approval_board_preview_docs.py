"""AION-144 v0.2 runtime approval board preview regression tests."""

from __future__ import annotations

import json
import os
import stat
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]

DOCS = [
    "docs/release/v02-runtime-approval-board-preview.md",
    "docs/release/v02-approval-vote-record-guard.md",
    "docs/release/v02-implementation-go-no-go-ledger-boundary.md",
    "docs/release/v02-runtime-approval-board-state-model.md",
    "docs/release/v02-runtime-approval-board-evidence-pack.md",
    "docs/release/v02-runtime-approval-board-no-go.md",
    "docs/release/v02-runtime-approval-board-checklist.md",
    "docs/adr/0135-v02-runtime-approval-board-preview.md",
]

EXAMPLES = [
    "examples/release/v02-runtime-approval-board-preview.json",
    "examples/release/v02-approval-vote-record-guard.json",
    "examples/release/v02-implementation-go-no-go-ledger-boundary.json",
    "examples/release/v02-runtime-approval-board-state-model.json",
    "examples/release/v02-runtime-approval-board-evidence-pack.json",
    "operator-console-static/demo-data/v02-runtime-approval-board-preview.json",
    "operator-console-static/demo-data/v02-implementation-go-no-go-ledger-boundary.json",
]

SCRIPTS = [
    "scripts/v02-runtime-approval-board-preview-check.sh",
    "scripts/v02-approval-vote-record-freeze.sh",
    "scripts/v02-runtime-approval-board-no-go-regression.sh",
]

TRUE_KEYS = {
    "v02_runtime_approval_board_preview_created",
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
    "runtime_approval_board_decision_approved",
    "approval_vote_record_approval",
    "approval_vote_record_runtime_effect",
    "implementation_go_status",
    "go_no_go_ledger_runtime_effect",
    "approval_docket_item_approved",
    "approval_docket_final_review_approval",
    "approval_docket_stabilization_approval",
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
    "request_package_implementation_approved",
    "proposal_template_implementation_approved",
    "approval_evidence_approval",
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


def test_v02_runtime_approval_board_docs_exist_and_are_indexed() -> None:
    for relative in DOCS:
        assert (ROOT / relative).exists(), relative

    assert "0135-v02-runtime-approval-board-preview.md" in _text(
        "docs/adr/README.md"
    )

    preview = _text("docs/release/v02-runtime-approval-board-preview.md")
    for required in [
        "## Purpose",
        "## Scope",
        "## Required Prior Gates",
        "## Runtime Approval Board Is Preview-Only",
        "## Runtime Approval Board Does Not Approve Implementation",
        "## Runtime Approval Board Does Not Enable Runtime",
        "## Required Approval Docket Fields",
        "## Required Implementation Decision Record Fields",
        "## Required Vote Record Fields",
        "## Required Go/No-Go Ledger Fields",
        "## Required Reviewer Evidence",
        "## Required ADR Dependency",
        "## Required Gate Dependency",
        "AION-144 creates no v0.2 tag and no v0.2 release.",
        "runtime_approval_board_decision_approved=false",
        "approval_vote_record_approval=false",
        "implementation_go_status=false",
        "runtime_implementation_approved=false",
    ]:
        assert required in preview

    vote = _text("docs/release/v02-approval-vote-record-guard.md")
    for required in [
        "approval_vote_record_created=true",
        "approval_vote_record_approval=false",
        "approval_vote_record_runtime_effect=false",
        "runtime_approval_board_decision_approved=false",
        "runtime_approval_lock_release_approved=false",
        "runtime_approval_review_approved=false",
        "implementation_decision_record_approval=false",
        "approval_docket_item_approved=false",
        "runtime_decision_readiness_approved=false",
        "runtime_implementation_approved=false",
        "decision_package_approval=false",
        "approval_readiness_approved=false",
        "review_board_decision_approval=false",
        "routing_decision_approval=false",
        "reviewer_signoff_implementation_approval=false",
        "v02_release_approved=false",
    ]:
        assert required in vote

    ledger = _text("docs/release/v02-implementation-go-no-go-ledger-boundary.md")
    for required in [
        "go_no_go_ledger_created=true",
        "implementation_go_status=false",
        "implementation_no_go_status=true",
        "go_no_go_ledger_runtime_effect=false",
        "runtime_approval_board_decision_approved=false",
        "runtime_approval_lock_release_approved=false",
        "implementation_decision_record_approval=false",
        "approval_docket_item_approved=false",
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
        assert required in ledger

    state_model = _text("docs/release/v02-runtime-approval-board-state-model.md")
    for state in [
        "drafted",
        "docketed",
        "vote_record_attached",
        "ledger_entry_attached",
        "evidence_attached",
        "quorum_preview",
        "approval_board_review_preview",
        "go_no_go_preview",
        "blocked",
        "rejected",
        "expired",
        "revoked",
        "approval_board_unapproved",
        "implementation_unapproved",
    ]:
        assert state in state_model
    assert "No state approves implementation or enables runtime." in state_model

    no_go = _text("docs/release/v02-runtime-approval-board-no-go.md")
    for condition in [
        "runtime approval board decision approved true",
        "approval vote record approval true",
        "approval vote record runtime effect true",
        "go/no-go ledger implementation go true",
        "go/no-go ledger runtime effect true",
        "approval docket final review approval true",
        "approval docket item approved true",
        "implementation decision record approval true",
        "runtime approval lock release approved true",
        "runtime approval review approved true",
        "decision package approval true",
        "review board decision approval true",
        "submission approval true",
        "request pack approval true",
        "implementation approval true",
        "approval workflow bypassed",
        "approval record missing",
        "ADR dependency bypassed",
        "gate dependency bypassed",
        "v0.2 tag created",
        "v0.2 release created",
        "runtime API execution routes added",
    ]:
        assert condition in no_go

    checklist = _text("docs/release/v02-runtime-approval-board-checklist.md")
    for item in [
        "docs complete",
        "examples valid",
        "scripts executable",
        "runtime approval board preview passing",
        "approval vote record freeze passing",
        "runtime approval board no-go passing",
        "approval docket final review passing",
        "decision package final review passing",
        "no runtime approval board decision approval",
        "no approval vote record approval",
        "no implementation go ledger entry",
        "no runtime implementation",
        "no v0.2 tag",
        "no v0.2 release",
        "no external calls",
        "no credentials/tokens",
        "no sandbox execution",
        "no package files",
        "no migrations",
    ]:
        assert item in checklist

    adr = _text("docs/adr/0135-v02-runtime-approval-board-preview.md")
    for required in [
        "Decision: add v0.2 runtime approval board preview.",
        "Decision: AION-144 does not approve implementation.",
        (
            "Decision: runtime approval board, approval vote records, and go/no-go "
            "ledger remain preview-only."
        ),
        "Decision: runtime approval board decision approval remains false.",
        "Decision: approval vote record approval remains false.",
        "Decision: go/no-go ledger implementation go remains false.",
        "Decision: runtime approval lock release approval remains false.",
        (
            "Decision: future implementation still requires explicit approval "
            "records, ADRs, and gate evidence."
        ),
        "Decision: no v0.2 release or tag is created.",
        (
            "Reason: AION needs a runtime approval board preview before any "
            "runtime approval decision can be considered."
        ),
        (
            "Consequence: future runtime candidates remain blocked until approval "
            "board, vote record, and go/no-go evidence exists and explicit "
            "approval records are created."
        ),
        "Constraint: no runtime enablement.",
        "Constraint: no external calls.",
        "Constraint: no credentials/tokens.",
        "Constraint: no sandbox execution.",
        "Constraint: no privileged bypass.",
    ]:
        assert required in adr


def test_v02_runtime_approval_board_examples_are_safe() -> None:
    for relative in EXAMPLES:
        payload = _json(relative)
        assert payload["task_id"] == "AION-144"
        assert payload["status"] == "passed"
        assert payload["synthetic"] is True
        for key in TRUE_KEYS:
            assert payload.get(key) is True, f"{relative}:{key}"
        for key in FALSE_KEYS:
            assert payload.get(key) is False, f"{relative}:{key}"
        assert set(payload["content_safety"]) == CONTENT_SAFETY
        _assert_false_keys(payload, relative)

        if relative.startswith("operator-console-static/"):
            assert payload["read_only"] is True
            assert payload["redaction_applied"] is True
            assert payload["sections"]
            assert payload["blockers"]
            assert isinstance(payload["warnings"], list)
            assert payload["refs"]
            actions = {item["action_key"]: item["allowed"] for item in payload["forbidden_actions"]}
            assert set(actions) == FORBIDDEN_ACTIONS
            assert all(value is False for value in actions.values())

        serialized = json.dumps(payload, sort_keys=True).lower()
        for marker in [
            "sk-",
            "ghp_",
            "xoxb-",
            "-----begin private key-----",
            "bearer ",
            "basic ",
            "api_key",
            "private_key",
            "access_token",
            "refresh_token",
            "id_token",
            "client_secret",
            "raw_prompt",
            "hidden_reasoning",
            "chain_of_thought",
        ]:
            assert marker not in serialized


def test_v02_runtime_approval_board_scripts_are_executable_and_pass() -> None:
    for relative in SCRIPTS:
        script = ROOT / relative
        assert script.exists(), relative
        assert os.access(script, os.X_OK), relative
        assert script.stat().st_mode & stat.S_IXUSR

    env = os.environ.copy()
    env["AION_V02_RUNTIME_APPROVAL_BOARD_PREVIEW_SKIP_INHERITED_GATES"] = "1"
    env["AION_V02_APPROVAL_VOTE_RECORD_FREEZE_SKIP_FULL_CHECK"] = "1"

    for relative, marker in [
        (
            "scripts/v02-runtime-approval-board-no-go-regression.sh",
            "v0.2 runtime approval board no-go regression PASS",
        ),
        (
            "scripts/v02-runtime-approval-board-preview-check.sh",
            "v0.2 runtime approval board preview check PASS",
        ),
        (
            "scripts/v02-approval-vote-record-freeze.sh",
            "v0.2 approval vote record freeze PASS",
        ),
    ]:
        result = subprocess.run(
            [str(ROOT / relative)],
            cwd=ROOT,
            env=env,
            check=True,
            capture_output=True,
            text=True,
        )
        assert marker in result.stdout


def _text(relative: str) -> str:
    return (ROOT / relative).read_text()


def _json(relative: str) -> dict[str, Any]:
    return json.loads((ROOT / relative).read_text())


def _assert_false_keys(value: Any, context: str) -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            if key in FALSE_KEYS:
                assert nested is False, f"{context}:{key}"
            if key in {
                "implementation_approval",
                "implementation_approved",
                "approval_state",
                "runtime_enabled",
                "release_approval",
                "approval_record_created",
            }:
                assert nested is False, f"{context}:{key}"
            _assert_false_keys(nested, context)
    elif isinstance(value, list):
        for nested in value:
            _assert_false_keys(nested, context)
