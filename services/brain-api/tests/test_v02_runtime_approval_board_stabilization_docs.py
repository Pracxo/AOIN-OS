"""AION-145 v0.2 runtime approval board stabilization regression tests."""

from __future__ import annotations

import json
import os
import stat
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]

DOCS = [
    "docs/release/v02-runtime-approval-board-stabilization-gate.md",
    "docs/release/v02-approval-vote-record-freeze.md",
    "docs/release/v02-implementation-go-no-go-ledger-evidence-baseline.md",
    "docs/release/v02-runtime-approval-board-lifecycle-evidence-matrix.md",
    "docs/release/v02-runtime-approval-board-stabilization-summary.md",
    "docs/release/v02-runtime-approval-board-stabilization-no-go.md",
    "docs/release/v02-runtime-approval-board-closeout-checklist.md",
    "docs/adr/0136-v02-runtime-approval-board-stabilization.md",
]

EXAMPLES = [
    "examples/release/v02-runtime-approval-board-stabilization-gate.json",
    "examples/release/v02-approval-vote-record-freeze.json",
    "examples/release/v02-implementation-go-no-go-ledger-evidence-baseline.json",
    "examples/release/v02-runtime-approval-board-lifecycle-evidence-matrix.json",
    "examples/release/v02-runtime-approval-board-stabilization-summary.json",
    "operator-console-static/demo-data/v02-runtime-approval-board-stabilization.json",
    "operator-console-static/demo-data/v02-approval-vote-record-freeze.json",
]

SCRIPTS = [
    "scripts/v02-runtime-approval-board-stabilization-gate.sh",
    "scripts/v02-approval-vote-record-stabilization-freeze.sh",
    "scripts/v02-runtime-approval-board-stabilization-no-go-regression.sh",
]

TRUE_KEYS = {
    "v02_runtime_approval_board_stabilized",
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
    "runtime_approval_board_stabilization_approval",
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


def test_v02_runtime_approval_board_stabilization_docs_exist_and_are_indexed() -> None:
    for relative in DOCS:
        assert (ROOT / relative).exists(), relative

    assert "0136-v02-runtime-approval-board-stabilization.md" in _text(
        "docs/adr/README.md"
    )

    gate = _text("docs/release/v02-runtime-approval-board-stabilization-gate.md")
    for required in [
        "## Purpose",
        "## Scope",
        "## Required Prior Gates",
        "## Runtime Approval Board Preview Evidence",
        "## Approval Vote Record Evidence",
        "## Go/No-Go Ledger Evidence",
        "## Runtime Approval Board Lifecycle Evidence",
        "## Approval Lock Checks",
        "## No-Go Conditions",
        "AION-145 creates no v0.2 tag and no v0.2 release.",
        "v02_runtime_approval_board_stabilized=true",
        "runtime_approval_board_preview_only=true",
        "runtime_approval_board_decision_approved=false",
        "runtime_approval_board_stabilization_approval=false",
        "approval_vote_record_approval=false",
        "implementation_go_status=false",
        "runtime_implementation_approved=false",
    ]:
        assert required in gate

    vote = _text("docs/release/v02-approval-vote-record-freeze.md")
    for required in [
        "Approval vote records do not approve implementation",
        "approval_vote_record_created=true",
        "approval_vote_record_approval=false",
        "approval_vote_record_runtime_effect=false",
        "runtime_approval_board_decision_approved=false",
        "runtime_approval_board_stabilization_approval=false",
        "go_no_go_ledger_runtime_effect=false",
        "implementation_go_status=false",
        "implementation_no_go_status=true",
        "runtime_approval_lock_release_approved=false",
        "runtime_approval_review_approved=false",
        "implementation_decision_record_approval=false",
        "approval_docket_item_approved=false",
        "runtime_decision_readiness_approved=false",
        "runtime_implementation_approved=false",
        "v02_release_approved=false",
    ]:
        assert required in vote

    ledger = _text(
        "docs/release/v02-implementation-go-no-go-ledger-evidence-baseline.md"
    )
    for required in [
        "production auth implementation candidate",
        "audit/provenance hardening candidate",
        "rollback/recovery candidate",
        "external call release gate candidate",
        "connector runtime implementation candidate",
        "credential store implementation candidate",
        "sandbox runtime implementation candidate",
        "operator write execution candidate",
        "module activation candidate",
        "production UI decision candidate",
        "implementation_go_status=false",
        "implementation_no_go_status=true",
        "go_no_go_ledger_runtime_effect=false",
    ]:
        assert required in ledger

    matrix = _text(
        "docs/release/v02-runtime-approval-board-lifecycle-evidence-matrix.md"
    )
    for required in [
        "Board state",
        "Required evidence",
        "Required reviewer",
        "Required ADR",
        "Required gate",
        "Runtime approval board decision state",
        "Approval vote record state",
        "Go/no-go ledger state",
        "Runtime enabled",
        "Release blocker if violated",
    ]:
        assert required in matrix

    summary = _text("docs/release/v02-runtime-approval-board-stabilization-summary.md")
    for required in [
        "runtime_approval_board_stabilized=true",
        "runtime_approval_board_preview_only=true",
        "runtime_approval_board_decision_approved=false",
        "runtime_approval_board_stabilization_approval=false",
        "approval_vote_record_created=true",
        "approval_vote_record_approval=false",
        "approval_vote_record_runtime_effect=false",
        "go_no_go_ledger_created=true",
        "implementation_go_status=false",
        "implementation_no_go_status=true",
        "go_no_go_ledger_runtime_effect=false",
        "runtime_approval_lock_release_approved=false",
        "runtime_approval_review_approved=false",
        "runtime_implementation_approved=false",
        "v02_tag_created=false",
        "v02_release_created=false",
    ]:
        assert required in summary

    no_go = _text("docs/release/v02-runtime-approval-board-stabilization-no-go.md")
    for condition in [
        "runtime approval board decision approved true",
        "runtime approval board stabilization approval true",
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
        "approval readiness approved true",
        "review board decision approval true",
        "routing decision approval true",
        "request pack approval true",
        "submission approval true",
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

    checklist = _text("docs/release/v02-runtime-approval-board-closeout-checklist.md")
    for required in [
        "docs complete",
        "examples valid",
        "scripts executable",
        "runtime approval board preview passing",
        "runtime approval board stabilization passing",
        "approval vote record freeze passing",
        "runtime approval board no-go passing",
        "no runtime approval board decision approval",
        "no runtime approval board stabilization approval",
        "no approval vote record approval",
        "no approval vote record runtime effect",
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
        assert required in checklist

    adr = _text("docs/adr/0136-v02-runtime-approval-board-stabilization.md")
    for required in [
        "Decision: add v0.2 runtime approval board stabilization gate.",
        "Decision: AION-145 does not approve implementation.",
        "Decision: runtime approval board, approval vote records, and go/no-go ledger",
        "Decision: runtime approval board decision approval remains false.",
        "Decision: approval vote record approval remains false.",
        "Decision: implementation go status remains false.",
        "Decision: go/no-go ledger runtime effect remains false.",
        "Decision: future implementation still requires explicit approval records, ADRs,",
        "Decision: no v0.2 release or tag is created.",
        "Reason: AION needs a stable runtime approval board baseline",
        "Consequence: future runtime candidates remain blocked",
        "Constraint: no runtime enablement.",
        "Constraint: no external calls.",
        "Constraint: no credentials/tokens.",
        "Constraint: no sandbox execution.",
        "Constraint: no privileged bypass.",
    ]:
        assert required in adr


def test_v02_runtime_approval_board_stabilization_examples_are_safe() -> None:
    for relative in EXAMPLES:
        payload = _json(relative)
        assert payload["task_id"] == "AION-145", relative
        assert payload["status"] == "passed", relative
        assert payload["synthetic"] is True, relative
        assert payload["read_only"] is True, relative
        assert payload["redaction_applied"] is True, relative
        for key in TRUE_KEYS:
            assert payload.get(key) is True, f"{relative}:{key}"
        for key in FALSE_KEYS:
            assert payload.get(key) is False, f"{relative}:{key}"
        assert set(payload["content_safety"]) == CONTENT_SAFETY, relative
        assert isinstance(payload["sections"], list) and payload["sections"], relative
        assert isinstance(payload["blockers"], list) and payload["blockers"], relative
        assert isinstance(payload["warnings"], list), relative
        assert isinstance(payload["refs"], list) and payload["refs"], relative
        actions = {item["action_key"]: item["allowed"] for item in payload["forbidden_actions"]}
        assert set(actions) == FORBIDDEN_ACTIONS
        assert all(value is False for value in actions.values())
        _assert_false_keys(payload, relative)

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


def test_v02_runtime_approval_board_stabilization_scripts_are_executable_and_pass() -> None:
    for relative in SCRIPTS:
        script = ROOT / relative
        assert script.exists(), relative
        assert os.access(script, os.X_OK), relative
        assert script.stat().st_mode & stat.S_IXUSR

    env = os.environ.copy()
    env["AION_V02_RUNTIME_APPROVAL_BOARD_STABILIZATION_SKIP_INHERITED_GATES"] = "1"
    env["AION_V02_APPROVAL_VOTE_RECORD_STABILIZATION_SKIP_FULL_CHECK"] = "1"

    for relative, marker in [
        (
            "scripts/v02-runtime-approval-board-stabilization-no-go-regression.sh",
            "v0.2 runtime approval board stabilization no-go regression PASS",
        ),
        (
            "scripts/v02-runtime-approval-board-stabilization-gate.sh",
            "v0.2 runtime approval board stabilization gate PASS",
        ),
        (
            "scripts/v02-approval-vote-record-stabilization-freeze.sh",
            "v0.2 approval vote record stabilization freeze PASS",
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
