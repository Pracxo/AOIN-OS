"""AION-136 v0.2 pre-approval review board regression tests."""

from __future__ import annotations

import json
import os
import stat
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]

DOCS = [
    "docs/release/v02-preapproval-review-board.md",
    "docs/release/v02-submission-review-routing.md",
    "docs/release/v02-reviewer-role-matrix.md",
    "docs/release/v02-decision-readiness-boundary.md",
    "docs/release/v02-review-board-evidence-pack.md",
    "docs/release/v02-review-board-no-go.md",
    "docs/release/v02-preapproval-review-checklist.md",
    "docs/adr/0127-v02-preapproval-review-board.md",
]

EXAMPLES = [
    "examples/release/v02-preapproval-review-board.json",
    "examples/release/v02-submission-review-routing.json",
    "examples/release/v02-reviewer-role-matrix.json",
    "examples/release/v02-decision-readiness-boundary.json",
    "examples/release/v02-review-board-evidence-pack.json",
    "operator-console-static/demo-data/v02-preapproval-review-board.json",
    "operator-console-static/demo-data/v02-submission-review-routing.json",
]

TRUE_KEYS = {
    "v02_preapproval_review_board_created",
    "review_board_planning_only",
    "submission_registry_preview_only",
    "preapproval_queue_preview_only",
    "proposal_registry_preview_only",
    "approval_queue_preview_only",
}

FALSE_KEYS = {
    "review_board_decision_approval",
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
    "decision_readiness_is_approval",
    "routing_readiness_is_approval",
    "reviewer_signoff_enables_runtime",
    "adr_readiness_approves_implementation",
    "gate_readiness_approves_implementation",
}


def test_v02_preapproval_review_board_docs_exist_and_are_indexed() -> None:
    for relative in DOCS:
        assert (ROOT / relative).exists(), relative

    assert "0127-v02-preapproval-review-board.md" in _text("docs/adr/README.md")

    board = _text("docs/release/v02-preapproval-review-board.md")
    for required in [
        "## Purpose",
        "## Scope",
        "Review board is planning-only.",
        "Review board does not approve implementation.",
        "Review board does not enable runtime.",
        "## Required Reviewer Roles",
        "## Required Evidence Before Routing",
        "## Required ADR Dependency",
        "## Required Gate Dependency",
        "## Required No-Go Acknowledgement",
        "## Review Decision States",
        "AION-136 creates no v0.2 tag and no v0.2 release.",
    ]:
        assert required in board

    routing = _text("docs/release/v02-submission-review-routing.md")
    for candidate in [
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
    ]:
        assert candidate in routing
    for column in [
        "Submission type",
        "Required reviewer roles",
        "Required ADR",
        "Required gate",
        "Required evidence",
        "Routing status",
        "Implementation approval",
        "Runtime enabled",
    ]:
        assert column in routing

    roles = _text("docs/release/v02-reviewer-role-matrix.md")
    for role in [
        "requester",
        "intake reviewer",
        "security reviewer",
        "architecture reviewer",
        "operator reviewer",
        "policy reviewer",
        "audit/provenance reviewer",
        "rollback reviewer",
        "approver placeholder",
        "auditor",
    ]:
        assert role in roles
    for column in [
        "Responsibility",
        "Decision boundary",
        "Cannot approve implementation alone",
        "Cannot enable runtime",
        "Evidence required",
        "Conflict-of-interest notes",
    ]:
        assert column in roles

    readiness = _text("docs/release/v02-decision-readiness-boundary.md")
    for required in [
        "Decision readiness is not approval.",
        "Routing readiness is not approval.",
        "Reviewer sign-off is not runtime enablement.",
        "ADR readiness is not implementation approval.",
        "Gate readiness is not implementation approval.",
        "Implementation approval remains false.",
        "Submission approval remains false.",
        "Preapproval queue approval remains false.",
        "Review board decision approval remains false.",
    ]:
        assert required in readiness

    evidence = _text("docs/release/v02-review-board-evidence-pack.md")
    for source in [
        "submission registry stabilization",
        "request pack final review",
        "request pack stabilization",
        "implementation request pack",
        "planning track closeout",
        "final planning release gate",
        "planning master checkpoint",
        "proposal registry stabilization",
        "docs and boundary checks",
    ]:
        assert source in evidence

    no_go = _text("docs/release/v02-review-board-no-go.md")
    for condition in [
        "review board decision approval true",
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

    checklist = _text("docs/release/v02-preapproval-review-checklist.md")
    for item in [
        "docs complete",
        "examples valid",
        "scripts executable",
        "submission registry stabilization passing",
        "pre-approval queue freeze passing",
        "review board no-go regression passing",
        "request pack final review passing",
        "request pack stabilization passing",
        "planning track closeout passing",
        "final planning release gate passing",
        "no review board approval",
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

    adr = _text("docs/adr/0127-v02-preapproval-review-board.md")
    for required in [
        "Decision: add v0.2 pre-approval review board.",
        "Decision: AION-136 does not approve implementation.",
        "Decision: review board routing remains planning-only.",
        "Decision: review board decisions cannot enable runtime.",
        "Decision: review board decision approval remains false.",
        "Decision: no v0.2 release or tag is created.",
        "AION needs a review routing boundary before implementation candidates "
        "can enter formal decision review.",
        "Future candidates must pass routing, evidence, reviewer, ADR, and gate "
        "checks before approval can be considered.",
        "Constraint: no runtime enablement.",
        "Constraint: no external calls.",
        "Constraint: no credentials/tokens.",
        "Constraint: no sandbox execution.",
        "Constraint: no privileged bypass.",
    ]:
        assert required in adr


def test_v02_preapproval_review_board_examples_are_safe() -> None:
    for relative in EXAMPLES:
        payload = _json(relative)
        assert payload["task_id"] == "AION-136"
        assert payload["status"] == "passed"
        assert payload["synthetic"] is True
        for key in TRUE_KEYS:
            assert payload[key] is True, f"{relative}.{key} must be true"
        _assert_false_keys(payload, relative)

    routing = _json("examples/release/v02-submission-review-routing.json")
    assert routing["routes"]
    for route in routing["routes"]:
        assert route["implementation_approval"] is False
        assert route["runtime_enabled"] is False

    roles = _json("examples/release/v02-reviewer-role-matrix.json")
    assert len(roles["roles"]) == 10
    for role in roles["roles"]:
        assert role["cannot_approve_implementation_alone"] is True
        assert role["cannot_enable_runtime"] is True

    evidence = _json("examples/release/v02-review-board-evidence-pack.json")
    assert len(evidence["evidence_sources"]) == 9

    for relative in EXAMPLES[-2:]:
        payload = _json(relative)
        assert payload["read_only"] is True
        assert payload["redaction_applied"] is True
        assert payload["sections"]
        assert payload["blockers"]
        assert payload["warnings"]
        assert payload["refs"]
        assert payload["forbidden_actions"]
        for action in payload["forbidden_actions"]:
            assert action["allowed"] is False


def test_v02_preapproval_review_board_scripts_are_executable_and_pass() -> None:
    scripts = [
        ROOT / "scripts/v02-preapproval-review-board-check.sh",
        ROOT / "scripts/v02-review-board-freeze.sh",
        ROOT / "scripts/v02-review-board-no-go-regression.sh",
    ]
    for script in scripts:
        assert script.exists(), script
        assert script.stat().st_mode & stat.S_IXUSR, script
        subprocess.run(["bash", "-n", str(script)], cwd=ROOT, check=True)

    env = {
        **os.environ,
        "AION_V02_PREAPPROVAL_REVIEW_BOARD_SKIP_INHERITED_GATES": "1",
        "AION_V02_REVIEW_BOARD_FREEZE_SKIP_FULL_CHECK": "1",
        "AION_V02_SUBMISSION_REGISTRY_STABILIZATION_SKIP_INHERITED_GATES": "1",
        "AION_V02_SUBMISSION_REGISTRY_FREEZE_SKIP_FULL_CHECK": "1",
        "AION_V02_SUBMISSION_REGISTRY_PREVIEW_SKIP_INHERITED_GATES": "1",
        "AION_V02_PREAPPROVAL_QUEUE_FREEZE_SKIP_FULL_CHECK": "1",
    }
    for command in [
        "./scripts/v02-preapproval-review-board-check.sh",
        "./scripts/v02-review-board-freeze.sh",
        "./scripts/v02-review-board-no-go-regression.sh",
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
            }:
                assert nested is False, f"{context}.{key} must be false"
            _assert_false_keys(nested, f"{context}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _assert_false_keys(item, f"{context}[{index}]")
