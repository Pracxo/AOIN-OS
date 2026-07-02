"""AION-123 v0.2 approval workflow stabilization regression tests."""

from __future__ import annotations

import json
import os
import stat
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]

DOCS = [
    "docs/release/v02-approval-workflow-stabilization-gate.md",
    "docs/release/v02-implementation-request-intake-validation.md",
    "docs/release/v02-approval-decision-evidence-matrix.md",
    "docs/release/v02-approval-expiry-revocation-model.md",
    "docs/release/v02-dual-control-review-model.md",
    "docs/release/v02-approval-workflow-no-go.md",
    "docs/release/v02-approval-workflow-stabilization-checklist.md",
    "docs/adr/0114-v02-approval-workflow-stabilization.md",
]

EXAMPLES = [
    "examples/release/v02-approval-workflow-stabilization-gate.json",
    "examples/release/v02-implementation-request-intake-validation.json",
    "examples/release/v02-approval-decision-evidence-matrix.json",
    "examples/release/v02-approval-expiry-revocation-model.json",
    "examples/release/v02-dual-control-review-model.json",
    "operator-console-static/demo-data/v02-approval-workflow-stabilization.json",
    "operator-console-static/demo-data/v02-implementation-request-intake.json",
]

FALSE_KEYS = {
    "runtime_implementation_approved",
    "operator_write_execution_approved",
    "connector_implementation_approved",
    "production_auth_approved",
    "module_activation_approved",
    "external_calls_approved",
    "credential_storage_approved",
    "token_storage_approved",
    "sandbox_execution_approved",
    "v02_tag_created",
    "v02_release_created",
    "v02_release_approved",
    "package_files_added",
    "migrations_added",
    "backlog_implementation_items_approved",
    "approval_workflow_bypassed",
    "adr_dependency_bypassed",
    "gate_dependency_bypassed",
    "approval_expiry_bypassed",
    "approval_revocation_bypassed",
    "dual_control_bypassed",
    "api_runtime_execution_route_added",
    "sdk_resource_implementation_added",
    "cli_command_implementation_added",
    "frontend_dependencies_added",
    "secrets_present",
    "credential_values_present",
    "token_values_present",
    "endpoints_present",
    "prompt_payloads_present",
    "private_reasoning_present",
}


def test_v02_approval_workflow_docs_exist_and_are_indexed() -> None:
    for relative in DOCS:
        assert (ROOT / relative).exists(), relative

    index = _text("docs/adr/README.md")
    assert "0114-v02-approval-workflow-stabilization.md" in index

    gate = _text("docs/release/v02-approval-workflow-stabilization-gate.md")
    for heading in [
        "## Purpose",
        "## Scope",
        "## Required Prior Gates",
        "## Approval Workflow Evidence",
        "## Intake Validation Evidence",
        "## Decision Record Evidence",
        "## Expiry And Revocation Evidence",
        "## Dual-Control Evidence",
        "## Implementation Approval Guard Checks",
        "## No-Go Conditions",
        "## No v0.2 Tag Or Release",
    ]:
        assert heading in gate
    assert "AION-123 explicitly creates no v0.2 tag and no release" in gate

    intake = _text("docs/release/v02-implementation-request-intake-validation.md")
    for required in [
        "## Required Request Fields",
        "## Workstream Classification",
        "## Runtime Capability Requested",
        "## Risk Statement",
        "## Security Impact",
        "## Policy Impact",
        "## Audit/Provenance Impact",
        "## Rollback Plan",
        "## ADR Dependency",
        "## Gate Dependency",
        "## Test Evidence",
        "## Rejection Conditions",
        "Default approval status: false.",
    ]:
        assert required in intake

    matrix = _text("docs/release/v02-approval-decision-evidence-matrix.md")
    for required in [
        "Workstream",
        "Required ADR",
        "Required Gate",
        "Required Evidence",
        "Required Reviewers",
        "Approval Status",
        "Runtime Approval Status",
        "Release Blocker If Violated",
        "Notes",
    ]:
        assert required in matrix

    expiry = _text("docs/release/v02-approval-expiry-revocation-model.md")
    for required in [
        "## Approval Expiry Rule",
        "## Approval Revocation Rule",
        "## Evidence Refresh Requirement",
        "## Re-Review Triggers",
        "## Expired Approval Behaviour",
        "## Revoked Approval Behaviour",
        "## Audit/Provenance Requirement",
        "## Approval Does Not Execute",
        "## Approval Does Not Enable Runtime By Itself",
    ]:
        assert required in expiry

    dual = _text("docs/release/v02-dual-control-review-model.md")
    for required in [
        "## Requester",
        "## Reviewer",
        "## Security Reviewer",
        "## Architecture Reviewer",
        "## Operator Reviewer",
        "## Approver",
        "## Auditor",
        "## Conflict-Of-Interest Rule",
        "## Dual-Control Option",
        "## Break-Glass Future-Only",
    ]:
        assert required in dual

    no_go = _text("docs/release/v02-approval-workflow-no-go.md")
    for condition in [
        "implementation approval set true",
        "backlog implementation approval set true",
        "approval workflow bypassed",
        "ADR dependency bypassed",
        "gate dependency bypassed",
        "approval expiry bypassed",
        "approval revocation bypassed",
        "dual-control bypassed",
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

    checklist = _text("docs/release/v02-approval-workflow-stabilization-checklist.md")
    for item in [
        "docs complete",
        "examples valid",
        "scripts executable",
        "kickoff boundary passing",
        "readiness final review passing",
        "planning stabilization passing",
        "post-v0.1 release candidate passing",
        "platform integration passing",
        "approval workflow guard passing",
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

    adr = _text("docs/adr/0114-v02-approval-workflow-stabilization.md")
    assert "Decision: add v0.2 approval workflow stabilization gate." in adr
    assert "Decision: AION-123 does not approve implementation." in adr
    assert "Decision: approval workflow stabilization does not enable runtime." in adr
    assert "Decision: future implementation still requires explicit approval records, ADRs," in adr
    assert "Decision: no v0.2 release or tag is created." in adr
    assert "Reason: AION needs a stable approval workflow before implementation work can be" in adr
    assert "Consequence: future runtime work must pass intake, decision, expiry," in adr
    assert "Constraint: no runtime enablement." in adr
    assert "Constraint: no external calls." in adr
    assert "Constraint: no credentials/tokens." in adr
    assert "Constraint: no sandbox execution." in adr
    assert "Constraint: no privileged bypass." in adr


def test_v02_approval_workflow_examples_are_safe() -> None:
    for relative in EXAMPLES:
        payload = _json(relative)
        if relative.startswith("examples/"):
            assert payload["synthetic"] is True
        assert payload["status"] == "passed"
        assert payload["task_id"] == "AION-123"
        assert payload["v02_approval_workflow_stabilized"] is True
        _assert_false_keys(payload, relative)


def test_v02_approval_workflow_scripts_are_executable_and_pass() -> None:
    for script in [
        ROOT / "scripts/v02-approval-workflow-stabilization-gate.sh",
        ROOT / "scripts/v02-approval-workflow-freeze.sh",
        ROOT / "scripts/v02-approval-workflow-no-go-regression.sh",
    ]:
        assert script.exists()
        assert os.access(script, os.X_OK)
        assert script.stat().st_mode & stat.S_IXUSR

    env = os.environ.copy()
    env["AION_V02_APPROVAL_WORKFLOW_SKIP_NESTED_GATES"] = "1"
    env["AION_V02_APPROVAL_WORKFLOW_FREEZE_SKIP_FULL_CHECK"] = "1"
    subprocess.run(
        ["./scripts/v02-approval-workflow-stabilization-gate.sh"],
        cwd=ROOT,
        env=env,
        check=True,
    )
    subprocess.run(
        ["./scripts/v02-approval-workflow-freeze.sh"],
        cwd=ROOT,
        env=env,
        check=True,
    )
    subprocess.run(
        ["./scripts/v02-approval-workflow-no-go-regression.sh"],
        cwd=ROOT,
        check=True,
    )


def _text(relative: str) -> str:
    return (ROOT / relative).read_text()


def _json(relative: str) -> dict[str, Any]:
    return json.loads(_text(relative))


def _assert_false_keys(value: Any, context: str) -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            if key in FALSE_KEYS:
                assert nested is False, f"{context}.{key} must be false"
            _assert_false_keys(nested, f"{context}.{key}")
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            _assert_false_keys(nested, f"{context}[{index}]")
