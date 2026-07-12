"""AION-149 v0.2 implementation authorization final review tests."""

from __future__ import annotations

import json
import os
import stat
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]

DOCS = [
    "docs/release/v02-implementation-authorization-final-review.md",
    "docs/release/v02-explicit-approval-record-closeout.md",
    "docs/release/v02-runtime-enablement-guard-final-lock.md",
    "docs/release/v02-authorization-final-evidence-matrix.md",
    "docs/release/v02-final-authorization-approval-guard.md",
    "docs/release/v02-implementation-authorization-final-no-go.md",
    "docs/release/v02-implementation-authorization-final-checklist.md",
    "docs/adr/0140-v02-implementation-authorization-final-review.md",
]

EXAMPLES = [
    "examples/release/v02-implementation-authorization-final-review.json",
    "examples/release/v02-explicit-approval-record-closeout.json",
    "examples/release/v02-runtime-enablement-guard-final-lock.json",
    "examples/release/v02-authorization-final-evidence-matrix.json",
    "examples/release/v02-final-authorization-approval-guard.json",
    "operator-console-static/demo-data/v02-implementation-authorization-final-review.json",
    "operator-console-static/demo-data/v02-runtime-enablement-guard-final-lock.json",
]

SCRIPTS = [
    "scripts/v02-implementation-authorization-final-review.sh",
    "scripts/v02-runtime-enablement-guard-final-freeze.sh",
    "scripts/v02-implementation-authorization-final-no-go-regression.sh",
]

TRUE_KEYS = {
    "v02_implementation_authorization_final_review_passed",
    "implementation_authorization_preview_only",
    "explicit_approval_record_created",
    "runtime_enablement_guard_created",
    "runtime_enablement_guard_final_lock_created",
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
    "implementation_authorization_stabilization_approval",
    "implementation_authorization_final_review_approval",
    "explicit_approval_record_approval",
    "explicit_approval_record_freeze_approval",
    "explicit_approval_record_closeout_approval",
    "runtime_enablement_guard_release_approved",
    "runtime_enablement_guard_final_lock_release_approved",
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


def test_v02_implementation_authorization_final_docs_exist() -> None:
    for relative in DOCS:
        assert (ROOT / relative).exists(), relative
    assert "0140-v02-implementation-authorization-final-review.md" in _text(
        "docs/adr/README.md"
    )

    final_review = _text("docs/release/v02-implementation-authorization-final-review.md")
    for required in [
        "## Purpose",
        "## Scope",
        "## Required prior gates",
        "## AION-147 summary",
        "## AION-148 summary",
        "## Implementation authorization final state",
        "## Explicit approval record final state",
        "## Runtime enablement guard final lock state",
        "## Authorization approval guard checks",
        "## No-go conditions",
        "AION-149 creates no v0.2 tag and no v0.2 release.",
    ]:
        assert required in final_review

    closeout = _text("docs/release/v02-explicit-approval-record-closeout.md")
    for required in [
        "Explicit approval records remain preview-only",
        "Explicit approval records do not approve implementation",
        "Explicit approval records do not enable runtime",
        "explicit_approval_record_created=true",
        "explicit_approval_record_approval=false",
        "explicit_approval_record_closeout_approval=false",
        "implementation_authorization_final_review_approval=false",
        "runtime_enablement_guard_release_approved=false",
        "runtime_implementation_approved=false",
        "v02_release_approved=false",
    ]:
        assert required in closeout

    final_lock = _text("docs/release/v02-runtime-enablement-guard-final-lock.md")
    for required in [
        "runtime_enablement_guard_created=true",
        "runtime_enablement_guard_final_lock_created=true",
        "runtime_enablement_guard_release_approved=false",
        "runtime_enablement_guard_final_lock_release_approved=false",
        "implementation_authorization_final_review_approval=false",
        "explicit_approval_record_closeout_approval=false",
        "operator_write_execution_approved=false",
        "connector_implementation_approved=false",
        "credential_storage_approved=false",
        "token_storage_approved=false",
        "sandbox_execution_approved=false",
    ]:
        assert required in final_lock


def test_v02_implementation_authorization_final_examples_are_locked() -> None:
    for relative in EXAMPLES:
        payload = _json(relative)
        assert payload["synthetic"] is True
        assert payload["read_only"] is True
        for key in TRUE_KEYS:
            assert payload.get(key) is True, f"{relative}: {key}"
        for key in FALSE_KEYS:
            assert payload.get(key) is False, f"{relative}: {key}"
        assert CONTENT_SAFETY <= set(payload.get("content_safety", []))


def test_v02_implementation_authorization_final_scripts_are_executable_and_pass() -> None:
    env = os.environ.copy()
    env["AION_V02_IMPLEMENTATION_AUTHORIZATION_FINAL_REVIEW_SKIP_INHERITED_GATES"] = "1"
    env["AION_V02_RUNTIME_ENABLEMENT_GUARD_FINAL_FREEZE_SKIP_FULL_CHECK"] = "1"
    env["AION_V02_IMPLEMENTATION_AUTHORIZATION_STABILIZATION_SKIP_INHERITED_GATES"] = "1"
    env["AION_V02_EXPLICIT_APPROVAL_RECORD_FREEZE_SKIP_FULL_CHECK"] = "1"
    env["AION_V02_IMPLEMENTATION_AUTHORIZATION_PREVIEW_SKIP_INHERITED_GATES"] = "1"
    env["AION_V02_RUNTIME_ENABLEMENT_GUARD_SKIP_FULL_CHECK"] = "1"
    for relative in SCRIPTS:
        path = ROOT / relative
        assert path.exists(), relative
        assert path.stat().st_mode & stat.S_IXUSR, relative
        subprocess.run([str(path)], cwd=ROOT, check=True, env=env)


def _json(relative: str) -> dict[str, Any]:
    return json.loads((ROOT / relative).read_text())


def _text(relative: str) -> str:
    return (ROOT / relative).read_text()
