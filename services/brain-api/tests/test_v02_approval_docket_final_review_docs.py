"""AION-143 v0.2 approval docket final review regression tests."""

from __future__ import annotations

import json
import os
import stat
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]

DOCS = [
    "docs/release/v02-approval-docket-final-review.md",
    "docs/release/v02-implementation-decision-record-closeout.md",
    "docs/release/v02-runtime-approval-lock.md",
    "docs/release/v02-approval-docket-final-evidence-matrix.md",
    "docs/release/v02-final-runtime-approval-guard.md",
    "docs/release/v02-approval-docket-final-no-go.md",
    "docs/release/v02-approval-docket-final-checklist.md",
    "docs/adr/0134-v02-approval-docket-final-review.md",
]

EXAMPLES = [
    "examples/release/v02-approval-docket-final-review.json",
    "examples/release/v02-implementation-decision-record-closeout.json",
    "examples/release/v02-runtime-approval-lock.json",
    "examples/release/v02-approval-docket-final-evidence-matrix.json",
    "examples/release/v02-final-runtime-approval-guard.json",
    "operator-console-static/demo-data/v02-approval-docket-final-review.json",
    "operator-console-static/demo-data/v02-runtime-approval-lock.json",
]

TRUE_KEYS = {
    "v02_approval_docket_final_review_passed",
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
    "approval_docket_item_approved",
    "approval_docket_final_review_approval",
    "approval_docket_stabilization_approval",
    "implementation_decision_record_approval",
    "implementation_decision_record_freeze_approval",
    "implementation_decision_record_closeout_approval",
    "runtime_approval_lock_release_approved",
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


def test_v02_approval_docket_final_review_docs_exist_and_are_indexed() -> None:
    for relative in DOCS:
        assert (ROOT / relative).exists(), relative

    assert "0134-v02-approval-docket-final-review.md" in _text("docs/adr/README.md")

    final_review = _text("docs/release/v02-approval-docket-final-review.md")
    for required in [
        "## Purpose",
        "## Scope",
        "## Required Prior Gates",
        "## AION-141 Summary",
        "## AION-142 Summary",
        "## Approval Docket Final State",
        "## Implementation Decision Record Final State",
        "## Runtime Approval Lock State",
        "## Approval Guard Checks",
        "## No-Go Conditions",
        "AION-143 creates no v0.2 tag and no v0.2 release.",
        "v02_approval_docket_final_review_passed=true",
        "approval_docket_final_review_approval=false",
        "runtime_approval_lock_release_approved=false",
        "runtime_implementation_approved=false",
    ]:
        assert required in final_review

    closeout = _text("docs/release/v02-implementation-decision-record-closeout.md")
    for required in [
        "Implementation decision records remain preview-only.",
        "Implementation decision records do not approve implementation",
        "Implementation decision records do not approve implementation and do not enable runtime.",
        "implementation_decision_record_created=true",
        "implementation_decision_record_approval=false",
        "implementation_decision_record_closeout_approval=false",
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
        "v02_release_approved=false",
    ]:
        assert required in closeout

    lock = _text("docs/release/v02-runtime-approval-lock.md")
    for required in [
        "runtime_approval_lock_created=true",
        "runtime_approval_lock_release_approved=false",
        "runtime_approval_review_approved=false",
        "runtime_decision_lock_release_approved=false",
        "runtime_decision_readiness_approved=false",
        "runtime_implementation_approved=false",
        "The lock does not enable connector runtime",
        "The lock creates no v0.2 tag and no v0.2 release.",
    ]:
        assert required in lock

    guard = _text("docs/release/v02-final-runtime-approval-guard.md")
    for required in [
        "approval docket final review is not implementation approval",
        "implementation decision record closeout is not implementation approval",
        "runtime approval lock is not runtime enablement",
        "explicit approval records remain required",
        "approval_docket_final_review_approval=false",
        "implementation_decision_record_closeout_approval=false",
        "runtime_approval_lock_release_approved=false",
    ]:
        assert required in guard

    no_go = _text("docs/release/v02-approval-docket-final-no-go.md")
    for condition in [
        "approval docket final review approval true",
        "approval docket item approved true",
        "implementation decision record closeout approval true",
        "runtime approval lock release approved true",
        "runtime approval review approved true",
        "runtime decision lock release approved true",
        "decision package approval true",
        "reviewer sign-off marked implementation approval true",
        "v0.2 tag created",
        "v0.2 release created",
        "runtime API execution routes added",
    ]:
        assert condition in no_go

    checklist = _text("docs/release/v02-approval-docket-final-checklist.md")
    for item in [
        "approval docket stabilization passing",
        "approval docket preview passing",
        "implementation decision record freeze passing",
        "no approval docket item approval",
        "no implementation decision record approval",
        "no runtime approval review approval",
        "no runtime approval lock release approval",
        "no runtime implementation",
        "no v0.2 tag",
        "no v0.2 release",
    ]:
        assert item in checklist

    adr = _text("docs/adr/0134-v02-approval-docket-final-review.md")
    for required in [
        "Decision: add v0.2 approval docket final review.",
        "Decision: AION-143 does not approve implementation.",
        "Decision: runtime approval lock does not enable runtime.",
        "Decision: approval docket item approval remains false.",
        "Decision: implementation decision record approval remains false.",
        "Decision: runtime approval review approval remains false.",
        "Decision: runtime approval lock release approval remains false.",
        "Decision: no v0.2 release or tag is created.",
        "Constraint: no runtime enablement.",
        "Constraint: no external calls.",
        "Constraint: no credentials/tokens.",
        "Constraint: no sandbox execution.",
        "Constraint: no privileged bypass.",
    ]:
        assert required in adr


def test_v02_approval_docket_final_review_examples_are_safe() -> None:
    for relative in EXAMPLES:
        payload = _json(relative)
        assert payload["task_id"] == "AION-143"
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
            actions = {item["action_key"]: item["allowed"] for item in payload["forbidden_actions"]}
            assert set(actions) == FORBIDDEN_ACTIONS
            assert all(value is False for value in actions.values())


def test_v02_approval_docket_final_review_static_console_wiring() -> None:
    html = _text("operator-console-static/index.html")
    app = _text("operator-console-static/app.js")
    readme = _text("operator-console-static/README.md")

    for marker in [
        "v02-approval-docket-final-review",
        "v02-runtime-approval-lock",
        "./scripts/v02-approval-docket-final-review.sh",
        "./scripts/v02-runtime-approval-lock-freeze.sh",
        "./scripts/v02-approval-docket-final-no-go-regression.sh",
    ]:
        assert marker in html
        assert marker in app

    assert "AION-143 v0.2 Approval Docket Final Review Panels" in readme
    assert "approval docket final review approval false" in readme
    assert "runtime approval lock release approval false" in readme


def test_v02_approval_docket_final_review_scripts_are_executable_and_pass() -> None:
    scripts = [
        "scripts/v02-approval-docket-final-review.sh",
        "scripts/v02-runtime-approval-lock-freeze.sh",
        "scripts/v02-approval-docket-final-no-go-regression.sh",
    ]
    env = os.environ.copy()
    env.update(
        {
            "AION_V02_APPROVAL_DOCKET_FINAL_REVIEW_SKIP_INHERITED_GATES": "1",
            "AION_V02_RUNTIME_APPROVAL_LOCK_FREEZE_SKIP_FULL_CHECK": "1",
            "AION_V02_APPROVAL_DOCKET_STABILIZATION_SKIP_INHERITED_GATES": "1",
            "AION_V02_IMPLEMENTATION_DECISION_RECORD_FREEZE_SKIP_FULL_CHECK": "1",
            "AION_V02_APPROVAL_DOCKET_PREVIEW_SKIP_INHERITED_GATES": "1",
            "AION_V02_RUNTIME_APPROVAL_REVIEW_FREEZE_SKIP_FULL_CHECK": "1",
            "AION_V02_DECISION_PACKAGE_FINAL_REVIEW_SKIP_INHERITED_GATES": "1",
            "AION_V02_RUNTIME_DECISION_LOCK_FREEZE_SKIP_FULL_CHECK": "1",
        }
    )
    for script in scripts:
        mode = (ROOT / script).stat().st_mode
        assert mode & stat.S_IXUSR, f"{script} must be executable"
        result = subprocess.run(
            [str(ROOT / script)],
            cwd=ROOT,
            env=env,
            capture_output=True,
            text=True,
            check=True,
        )
        assert "PASS" in result.stdout


def _json(relative: str) -> dict[str, Any]:
    return json.loads((ROOT / relative).read_text())


def _text(relative: str) -> str:
    return (ROOT / relative).read_text()


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
        for index, nested in enumerate(value):
            _assert_false_keys(nested, f"{context}[{index}]")
