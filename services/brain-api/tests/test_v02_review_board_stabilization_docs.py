"""AION-137 v0.2 review board stabilization regression tests."""

from __future__ import annotations

import json
import os
import stat
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]

DOCS = [
    "docs/release/v02-review-board-stabilization-gate.md",
    "docs/release/v02-review-routing-freeze.md",
    "docs/release/v02-reviewer-quorum-model.md",
    "docs/release/v02-decision-readiness-evidence-baseline.md",
    "docs/release/v02-review-board-closeout-checklist.md",
    "docs/release/v02-review-routing-no-go.md",
    "docs/release/v02-review-board-stabilization-summary.md",
    "docs/adr/0128-v02-review-board-stabilization.md",
]

EXAMPLES = [
    "examples/release/v02-review-board-stabilization-gate.json",
    "examples/release/v02-review-routing-freeze.json",
    "examples/release/v02-reviewer-quorum-model.json",
    "examples/release/v02-decision-readiness-evidence-baseline.json",
    "examples/release/v02-review-board-closeout-result.json",
    "operator-console-static/demo-data/v02-review-board-stabilization.json",
    "operator-console-static/demo-data/v02-review-routing-freeze.json",
]

TRUE_KEYS = {
    "v02_review_board_stabilized",
    "review_board_planning_only",
    "submission_registry_preview_only",
    "preapproval_queue_preview_only",
    "proposal_registry_preview_only",
    "approval_queue_preview_only",
}

FALSE_KEYS = {
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


def test_v02_review_board_stabilization_docs_exist_and_are_indexed() -> None:
    for relative in DOCS:
        assert (ROOT / relative).exists(), relative

    assert "0128-v02-review-board-stabilization.md" in _text("docs/adr/README.md")

    gate = _text("docs/release/v02-review-board-stabilization-gate.md")
    for required in [
        "## Purpose",
        "## Scope",
        "## Required Prior Gates",
        "## Review Board Evidence",
        "## Routing Evidence",
        "## Reviewer Role Evidence",
        "## Decision Readiness Evidence",
        "## Approval Lock Checks",
        "## No-Go Conditions",
        "AION-137 creates no v0.2 tag and no v0.2 release.",
    ]:
        assert required in gate

    routing = _text("docs/release/v02-review-routing-freeze.md")
    for required in [
        "Routing remains planning-only.",
        "Routing does not approve implementation.",
        "Routing does not enable runtime.",
        "Reviewer assignment does not approve implementation.",
        "Reviewer sign-off does not enable runtime.",
        "Review board decision approval remains false.",
        "Submission approval remains false.",
        "Pre-approval queue approval remains false.",
        "## Required ADR Dependency",
        "## Required Gate Dependency",
        "## No-Go Conditions",
    ]:
        assert required in routing

    quorum = _text("docs/release/v02-reviewer-quorum-model.md")
    for role in [
        "Requester",
        "Intake reviewer",
        "Security reviewer",
        "Architecture reviewer",
        "Operator reviewer",
        "Policy reviewer",
        "Audit/provenance reviewer",
        "Rollback reviewer",
        "Approver placeholder",
        "Auditor",
        "## Quorum Expectation",
        "## Conflict-of-Interest Rule",
        "## Dual-Control Option",
        "No reviewer can approve implementation alone.",
        "No reviewer can enable runtime.",
    ]:
        assert role in quorum

    readiness = _text("docs/release/v02-decision-readiness-evidence-baseline.md")
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
        assert candidate in readiness
    for column in [
        "Submission status",
        "Routing status",
        "Reviewer evidence required",
        "Decision readiness status",
        "Review board approval",
        "Implementation approval",
        "Required ADR",
        "Required gate",
        "Blocker",
        "## Next Planning Action",
    ]:
        assert column in readiness

    checklist = _text("docs/release/v02-review-board-closeout-checklist.md")
    for item in [
        "docs complete",
        "examples valid",
        "scripts executable",
        "pre-approval review board check passing",
        "review board freeze passing",
        "review board no-go regression passing",
        "submission registry stabilization passing",
        "submission registry preview passing",
        "request pack final review passing",
        "planning track closeout passing",
        "final planning release gate passing",
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

    no_go = _text("docs/release/v02-review-routing-no-go.md")
    for condition in [
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

    summary = _text("docs/release/v02-review-board-stabilization-summary.md")
    for required in [
        "review_board_stabilized=true",
        "review_board_planning_only=true",
        "review_board_decision_approval=false",
        "routing_decision_approval=false",
        "reviewer_signoff_implementation_approval=false",
        "submission_registry_preview_only=true",
        "preapproval_queue_preview_only=true",
        "preapproval_queue_item_approved=false",
        "request_pack_approval=false",
        "submission_approval=false",
        "runtime_implementation_approved=false",
        "workstream_implementation_approved=false",
        "proposal_implementation_approved=false",
        "v02_tag_created=false",
        "v02_release_created=false",
    ]:
        assert required in summary

    adr = _text("docs/adr/0128-v02-review-board-stabilization.md")
    for required in [
        "Decision: add v0.2 review board stabilization gate.",
        "Decision: AION-137 does not approve implementation.",
        "Decision: review board and routing remain planning-only.",
        "Decision: review board decision approval remains false.",
        "Decision: routing and reviewer sign-off cannot enable runtime.",
        "Decision: future implementation still requires explicit approval "
        "records, ADRs, and gate evidence.",
        "Decision: no v0.2 release or tag is created.",
        "AION needs a stable review board baseline before implementation "
        "approval can be considered.",
        "Future implementation candidates remain blocked until review routing "
        "and approval evidence are complete.",
        "Constraint: no runtime enablement.",
        "Constraint: no external calls.",
        "Constraint: no credentials/tokens.",
        "Constraint: no sandbox execution.",
        "Constraint: no privileged bypass.",
    ]:
        assert required in adr


def test_v02_review_board_stabilization_examples_are_safe() -> None:
    for relative in EXAMPLES:
        payload = _json(relative)
        assert payload["task_id"] == "AION-137"
        assert payload["status"] == "passed"
        assert payload["synthetic"] is True
        for key in TRUE_KEYS:
            assert payload[key] is True, f"{relative}.{key} must be true"
        _assert_false_keys(payload, relative)

    routing = _json("examples/release/v02-review-routing-freeze.json")
    assert routing["routes"]
    for route in routing["routes"]:
        assert route["implementation_approval"] is False
        assert route["runtime_enabled"] is False
        assert route["review_board_decision_approval"] is False
        assert route["routing_decision_approval"] is False

    quorum = _json("examples/release/v02-reviewer-quorum-model.json")
    assert len(quorum["roles"]) == 10
    assert quorum["no_reviewer_can_approve_implementation_alone"] is True
    assert quorum["no_reviewer_can_enable_runtime"] is True

    readiness = _json("examples/release/v02-decision-readiness-evidence-baseline.json")
    assert len(readiness["candidates"]) == 10
    assert readiness["decision_readiness_status"] == "evidence baseline only"

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


def test_v02_review_board_stabilization_scripts_are_executable_and_pass() -> None:
    scripts = [
        ROOT / "scripts/v02-review-board-stabilization-gate.sh",
        ROOT / "scripts/v02-review-routing-freeze.sh",
        ROOT / "scripts/v02-review-board-stabilization-no-go-regression.sh",
    ]
    for script in scripts:
        assert script.exists(), script
        assert script.stat().st_mode & stat.S_IXUSR, script
        subprocess.run(["bash", "-n", str(script)], cwd=ROOT, check=True)

    env = {
        **os.environ,
        "AION_V02_REVIEW_BOARD_STABILIZATION_SKIP_INHERITED_GATES": "1",
        "AION_V02_REVIEW_ROUTING_FREEZE_SKIP_FULL_CHECK": "1",
        "AION_V02_PREAPPROVAL_REVIEW_BOARD_SKIP_INHERITED_GATES": "1",
        "AION_V02_REVIEW_BOARD_FREEZE_SKIP_FULL_CHECK": "1",
        "AION_V02_SUBMISSION_REGISTRY_STABILIZATION_SKIP_INHERITED_GATES": "1",
        "AION_V02_SUBMISSION_REGISTRY_FREEZE_SKIP_FULL_CHECK": "1",
        "AION_V02_SUBMISSION_REGISTRY_PREVIEW_SKIP_INHERITED_GATES": "1",
        "AION_V02_PREAPPROVAL_QUEUE_FREEZE_SKIP_FULL_CHECK": "1",
    }
    for command in [
        "./scripts/v02-review-board-stabilization-gate.sh",
        "./scripts/v02-review-routing-freeze.sh",
        "./scripts/v02-review-board-stabilization-no-go-regression.sh",
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
