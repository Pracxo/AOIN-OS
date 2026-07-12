"""AION-150 v0.2 authorization track closeout tests."""

from __future__ import annotations

import json
import os
import stat
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]

DOCS = [
    "docs/release/v02-authorization-track-closeout-report.md",
    "docs/release/v02-approval-chain-master-evidence.md",
    "docs/release/v02-runtime-enablement-master-lock.md",
    "docs/release/v02-explicit-approval-record-master-ledger.md",
    "docs/release/v02-implementation-authorization-final-status.md",
    "docs/release/v02-authorization-track-closeout-no-go.md",
    "docs/release/v02-authorization-track-closeout-checklist.md",
    "docs/adr/0141-v02-authorization-track-closeout.md",
]

EXAMPLES = [
    "examples/release/v02-authorization-track-closeout-report.json",
    "examples/release/v02-approval-chain-master-evidence.json",
    "examples/release/v02-runtime-enablement-master-lock.json",
    "examples/release/v02-explicit-approval-record-master-ledger.json",
    "examples/release/v02-implementation-authorization-final-status.json",
    "operator-console-static/demo-data/v02-authorization-track-closeout.json",
    "operator-console-static/demo-data/v02-runtime-enablement-master-lock.json",
]

SCRIPTS = [
    "scripts/v02-authorization-track-closeout.sh",
    "scripts/v02-runtime-enablement-master-lock-freeze.sh",
    "scripts/v02-authorization-track-closeout-no-go-regression.sh",
]

TRUE_KEYS = {
    "v02_authorization_track_closeout_passed",
    "authorization_governance_baseline_complete",
    "implementation_authorization_preview_only",
    "explicit_approval_record_created",
    "runtime_enablement_master_lock_created",
    "runtime_enablement_guard_created",
    "runtime_enablement_guard_final_lock_created",
    "implementation_no_go_status",
}

FALSE_KEYS = {
    "implementation_authorization_approved",
    "implementation_authorization_stabilization_approval",
    "implementation_authorization_final_review_approval",
    "explicit_approval_record_approval",
    "explicit_approval_record_freeze_approval",
    "explicit_approval_record_closeout_approval",
    "runtime_enablement_master_lock_release_approved",
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
    "implementation_decision_record_approval",
    "implementation_decision_record_closeout_approval",
    "runtime_approval_review_approved",
    "runtime_approval_lock_release_approved",
    "decision_package_approval",
    "approval_readiness_approved",
    "review_board_decision_approval",
    "routing_decision_approval",
    "reviewer_signoff_implementation_approval",
    "request_pack_approval",
    "submission_approval",
    "preapproval_queue_item_approved",
    "runtime_implementation_approved",
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
    "v02_tag_created",
    "v02_release_created",
    "v02_release_approved",
}

CONTENT_SAFETY = {
    "no secrets",
    "no tokens",
    "no credentials",
    "no endpoints",
    "no raw prompts",
    "no hidden reasoning",
}


def test_v02_authorization_track_closeout_docs_exist() -> None:
    for relative in DOCS:
        assert (ROOT / relative).exists(), relative
    assert "0141-v02-authorization-track-closeout.md" in _text("docs/adr/README.md")

    report = _text("docs/release/v02-authorization-track-closeout-report.md")
    for required in [
        "## Purpose",
        "## Scope",
        "## AION-141 through AION-149 summary",
        "## Approval docket final state",
        "## Runtime approval board final state",
        "## Implementation authorization final state",
        "## Explicit approval record final state",
        "## Runtime enablement guard final state",
        "## Current implementation state",
        "## Remaining blockers",
        "## Closeout decision",
        "authorization governance baseline complete",
        "runtime implementation unapproved",
        "implementation authorization unapproved",
        "runtime enablement guards locked",
        "implementation go status false",
        "future implementation requires a separate, explicit approval transaction",
        "no v0.2 tag",
        "no v0.2 release",
    ]:
        assert required in report

    master_lock = _text("docs/release/v02-runtime-enablement-master-lock.md")
    for required in [
        "runtime_enablement_master_lock_created=true",
        "runtime_enablement_master_lock_release_approved=false",
        "runtime_enablement_guard_release_approved=false",
        "runtime_enablement_guard_final_lock_release_approved=false",
        "runtime_implementation_approved=false",
        "implementation_authorization_approved=false",
        "explicit_approval_record_approval=false",
        "runtime_approval_board_decision_approved=false",
        "approval_vote_record_approval=false",
        "implementation_go_status=false",
        "implementation_no_go_status=true",
    ]:
        assert required in master_lock

    final_status = _text(
        "docs/release/v02-implementation-authorization-final-status.md"
    )
    for required in [
        "authorization_track_closed_out=true",
        "authorization_governance_baseline_complete=true",
        "implementation_authorization_preview_only=true",
        "implementation_authorization_approved=false",
        "implementation_authorization_final_review_approval=false",
        "runtime_enablement_master_lock_created=true",
        "runtime_enablement_master_lock_release_approved=false",
        "runtime_approval_board_decision_approved=false",
        "approval_vote_record_approval=false",
        "implementation_go_status=false",
        "implementation_no_go_status=true",
        "runtime_implementation_approved=false",
        "v02_tag_created=false",
        "v02_release_created=false",
    ]:
        assert required in final_status


def test_v02_authorization_track_closeout_examples_are_locked() -> None:
    for relative in EXAMPLES:
        payload = _json(relative)
        assert payload["task_id"] == "AION-150"
        assert payload["synthetic"] is True
        assert payload["read_only"] is True
        for key in TRUE_KEYS:
            assert payload.get(key) is True, f"{relative}: {key}"
        for key in FALSE_KEYS:
            assert payload.get(key) is False, f"{relative}: {key}"
        assert CONTENT_SAFETY <= set(payload.get("content_safety", []))


def test_v02_authorization_track_closeout_scripts_are_executable_and_pass() -> None:
    env = os.environ.copy()
    env["AION_V02_AUTHORIZATION_TRACK_CLOSEOUT_SKIP_INHERITED_GATES"] = "1"
    env["AION_V02_RUNTIME_ENABLEMENT_MASTER_LOCK_FREEZE_SKIP_FULL_CHECK"] = "1"
    env["AION_V02_IMPLEMENTATION_AUTHORIZATION_FINAL_REVIEW_SKIP_INHERITED_GATES"] = (
        "1"
    )
    env["AION_V02_RUNTIME_ENABLEMENT_GUARD_FINAL_FREEZE_SKIP_FULL_CHECK"] = "1"
    env["AION_V02_IMPLEMENTATION_AUTHORIZATION_STABILIZATION_SKIP_INHERITED_GATES"] = (
        "1"
    )
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
