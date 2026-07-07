"""AION-146 v0.2 runtime approval board final review regression tests."""

from __future__ import annotations

import json
import os
import stat
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]

DOCS = [
    "docs/release/v02-runtime-approval-board-final-review.md",
    "docs/release/v02-approval-vote-record-closeout.md",
    "docs/release/v02-implementation-go-no-go-ledger-final-lock.md",
    "docs/release/v02-runtime-approval-board-final-evidence-matrix.md",
    "docs/release/v02-final-implementation-go-guard.md",
    "docs/release/v02-runtime-approval-board-final-no-go.md",
    "docs/release/v02-runtime-approval-board-final-checklist.md",
    "docs/adr/0137-v02-runtime-approval-board-final-review.md",
]

EXAMPLES = [
    "examples/release/v02-runtime-approval-board-final-review.json",
    "examples/release/v02-approval-vote-record-closeout.json",
    "examples/release/v02-implementation-go-no-go-ledger-final-lock.json",
    "examples/release/v02-runtime-approval-board-final-evidence-matrix.json",
    "examples/release/v02-final-implementation-go-guard.json",
    "operator-console-static/demo-data/v02-runtime-approval-board-final-review.json",
    "operator-console-static/demo-data/v02-implementation-go-no-go-ledger-final-lock.json",
]

SCRIPTS = [
    "scripts/v02-runtime-approval-board-final-review.sh",
    "scripts/v02-implementation-go-no-go-final-freeze.sh",
    "scripts/v02-runtime-approval-board-final-no-go-regression.sh",
]

TRUE_KEYS = {
    "v02_runtime_approval_board_final_review_passed",
    "runtime_approval_board_preview_only",
    "approval_vote_record_created",
    "go_no_go_ledger_created",
    "go_no_go_ledger_final_lock_created",
    "implementation_no_go_status",
    "implementation_no_go_final_status",
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


def test_v02_runtime_approval_board_final_docs_exist_and_are_indexed() -> None:
    for relative in DOCS:
        assert (ROOT / relative).exists(), relative

    assert "0137-v02-runtime-approval-board-final-review.md" in _text(
        "docs/adr/README.md"
    )

    gate = _text("docs/release/v02-runtime-approval-board-final-review.md")
    for required in [
        "## Purpose",
        "## Scope",
        "## Required Prior Gates",
        "## AION-144 Summary",
        "## AION-145 Summary",
        "## Runtime Approval Board Final State",
        "## Approval Vote Record Final State",
        "## Go/No-Go Ledger Final State",
        "## Implementation Go Guard Checks",
        "## No-Go Conditions",
        "AION-146 creates no v0.2 tag and no v0.2 release.",
        "v02_runtime_approval_board_final_review_passed=true",
        "runtime_approval_board_preview_only=true",
        "runtime_approval_board_decision_approved=false",
        "runtime_approval_board_final_review_approval=false",
        "approval_vote_record_closeout_approval=false",
        "implementation_go_status=false",
        "implementation_go_final_approval=false",
        "runtime_implementation_approved=false",
    ]:
        assert required in gate

    vote = _text("docs/release/v02-approval-vote-record-closeout.md")
    for required in [
        "Approval vote records remain preview-only",
        "Approval vote records do not approve implementation",
        "Approval vote records do not enable runtime",
        "approval_vote_record_created=true",
        "approval_vote_record_approval=false",
        "approval_vote_record_closeout_approval=false",
        "approval_vote_record_runtime_effect=false",
        "runtime_approval_board_final_review_approval=false",
        "implementation_go_status=false",
        "implementation_no_go_status=true",
        "runtime_implementation_approved=false",
        "v02_release_approved=false",
    ]:
        assert required in vote

    ledger = _text("docs/release/v02-implementation-go-no-go-ledger-final-lock.md")
    for required in [
        "go_no_go_ledger_created=true",
        "go_no_go_ledger_final_lock_created=true",
        "implementation_go_status=false",
        "implementation_no_go_status=true",
        "implementation_go_final_approval=false",
        "implementation_no_go_final_status=true",
        "runtime_approval_board_final_review_approval=false",
        "operator_write_execution_approved=false",
        "connector_implementation_approved=false",
        "production_auth_approved=false",
        "module_activation_approved=false",
        "external_calls_approved=false",
        "credential_storage_approved=false",
        "token_storage_approved=false",
        "sandbox_execution_approved=false",
    ]:
        assert required in ledger

    matrix = _text("docs/release/v02-runtime-approval-board-final-evidence-matrix.md")
    for required in [
        "Area",
        "Required evidence",
        "Required reviewer",
        "Required ADR",
        "Required gate",
        "Runtime approval board decision state",
        "Approval vote record state",
        "Go/no-go ledger state",
        "Implementation go state",
        "Runtime enabled",
        "Release blocker if violated",
    ]:
        assert required in matrix

    guard = _text("docs/release/v02-final-implementation-go-guard.md")
    for required in [
        "runtime approval board final review is not implementation approval",
        "approval vote record closeout is not implementation approval",
        "go/no-go ledger final lock is not runtime enablement",
        "implementation go status remains false",
        "implementation no-go status remains true",
        "reviewer sign-off is not implementation approval",
        "ADR dependency presence is not runtime enablement",
        "gate dependency success is not runtime enablement",
        "explicit approval records remain required",
        "all approval states remain false",
    ]:
        assert required in guard


def test_v02_runtime_approval_board_final_examples_are_locked() -> None:
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


def test_v02_runtime_approval_board_final_scripts_are_executable_and_pass() -> None:
    for relative in SCRIPTS:
        script = ROOT / relative
        assert script.exists(), relative
        assert os.access(script, os.X_OK), relative
        assert script.stat().st_mode & stat.S_IXUSR

    env = {
        **os.environ,
        "AION_V02_RUNTIME_APPROVAL_BOARD_FINAL_REVIEW_SKIP_INHERITED_GATES": "1",
        "AION_V02_IMPLEMENTATION_GO_NO_GO_FINAL_SKIP_FULL_CHECK": "1",
    }
    expected = {
        "scripts/v02-runtime-approval-board-final-review.sh": (
            "v0.2 runtime approval board final review PASS"
        ),
        "scripts/v02-implementation-go-no-go-final-freeze.sh": (
            "v0.2 implementation go/no-go final freeze PASS"
        ),
        "scripts/v02-runtime-approval-board-final-no-go-regression.sh": (
            "v0.2 runtime approval board final no-go regression PASS"
        ),
    }
    for relative, marker in expected.items():
        result = subprocess.run(
            [str(ROOT / relative)],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
            env=env,
        )
        assert marker in result.stdout


def _json(relative: str) -> dict[str, Any]:
    return json.loads((ROOT / relative).read_text())


def _text(relative: str) -> str:
    return (ROOT / relative).read_text()


def _assert_nested_false(value: Any) -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            if key in FALSE_KEYS:
                assert nested is False, key
            if key in {
                "implementation_approval",
                "implementation_approved",
                "approval_state",
                "runtime_enabled",
                "runtime_effect",
                "allowed",
                "go",
            } and isinstance(nested, bool):
                assert nested is False, key
            _assert_nested_false(nested)
    elif isinstance(value, list):
        for item in value:
            _assert_nested_false(item)
