"""AION-122 v0.2 implementation kickoff boundary regression tests."""

from __future__ import annotations

import json
import os
import stat
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]

DOCS = [
    "docs/release/v02-implementation-kickoff-boundary.md",
    "docs/release/v02-approval-workflow-blueprint.md",
    "docs/release/v02-runtime-workstream-lock.md",
    "docs/release/v02-implementation-request-template.md",
    "docs/release/v02-approval-decision-record.md",
    "docs/release/v02-workstream-sequencing-plan.md",
    "docs/release/v02-implementation-kickoff-no-go.md",
    "docs/adr/0113-v02-implementation-kickoff-boundary.md",
]

EXAMPLES = [
    "examples/release/v02-implementation-kickoff-boundary.json",
    "examples/release/v02-approval-workflow-blueprint.json",
    "examples/release/v02-runtime-workstream-lock.json",
    "examples/release/v02-implementation-request-template.json",
    "examples/release/v02-approval-decision-record.json",
    "operator-console-static/demo-data/v02-implementation-kickoff-boundary.json",
    "operator-console-static/demo-data/v02-runtime-workstream-lock.json",
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


def test_v02_implementation_kickoff_docs_exist_and_are_indexed() -> None:
    for relative in DOCS:
        assert (ROOT / relative).exists(), relative

    index = _text("docs/adr/README.md")
    assert "0113-v02-implementation-kickoff-boundary.md" in index

    boundary = _text("docs/release/v02-implementation-kickoff-boundary.md")
    for heading in [
        "## Purpose",
        "## Scope",
        "## Current Readiness State",
        "## Implementation Remains Unapproved",
        "## Required Approval Workflow",
        "## Required ADR Workflow",
        "## Required Gate Evidence",
        "## Blocked Runtime Areas",
        "## Kickoff Criteria",
        "## No-Go Conditions",
        "## No v0.2 Tag Or Release",
    ]:
        assert heading in boundary
    assert "AION-122 explicitly creates no v0.2 tag and no release" in boundary

    blueprint = _text("docs/release/v02-approval-workflow-blueprint.md")
    for required in [
        "## Requester Role",
        "## Reviewer Role",
        "## Approver Role",
        "## Security Reviewer Role",
        "## Architecture Reviewer Role",
        "## Operator Reviewer Role",
        "## Evidence Required Before Approval",
        "## Dual-Control Option",
        "## Approval Expiry",
        "## Approval Revocation",
        "## Approval Does Not Execute",
        "## Approval Does Not Enable Runtime By Itself",
        "## No-Go Conditions",
    ]:
        assert required in blueprint

    lock = _text("docs/release/v02-runtime-workstream-lock.md")
    for required in [
        "production_auth_implementation_locked=true",
        "connector_runtime_implementation_locked=true",
        "operator_write_execution_locked=true",
        "module_activation_locked=true",
        "external_calls_locked=true",
        "credential_storage_locked=true",
        "token_storage_locked=true",
        "sandbox_execution_locked=true",
        "runtime_route_registration_locked=true",
        "package_dependency_additions_locked=true",
        "migrations_locked=true",
    ]:
        assert required in lock

    request = _text("docs/release/v02-implementation-request-template.md")
    for required in [
        "## Workstream",
        "## Problem Statement",
        "## Proposed Change",
        "## Runtime Capability Requested",
        "## Security Impact",
        "## Policy Impact",
        "## Audit/Provenance Impact",
        "## Rollback Plan",
        "## ADR Dependency",
        "## Gate Dependency",
        "## Test Evidence",
        "## No-Go Acknowledgement",
        "## Approval Status",
    ]:
        assert required in request
    assert "Default approval status: false." in request

    decision = _text("docs/release/v02-approval-decision-record.md")
    for required in [
        "## Decision ID",
        "## Requested Workstream",
        "## Decision Status",
        "## Approval Status",
        "## Required ADR",
        "## Required Gate",
        "## Evidence Links",
        "## Reviewers",
        "## Expiry",
        "## Revocation Path",
        "## Notes",
        "## Default Decision",
        "Default decision: not approved.",
    ]:
        assert required in decision

    sequence = _text("docs/release/v02-workstream-sequencing-plan.md")
    for item in [
        "1. Production auth implementation planning",
        "2. Audit/provenance hardening",
        "3. Rollback/recovery design",
        "4. External call release gate design",
        "5. Connector runtime implementation planning",
        "6. Credential store implementation planning",
        "7. Sandbox runtime implementation planning",
        "8. Operator write execution planning",
        "9. Module activation planning",
        "10. Production UI decision",
        "implementation-unapproved",
    ]:
        assert item in sequence

    no_go = _text("docs/release/v02-implementation-kickoff-no-go.md")
    for condition in [
        "v0.2 tag created",
        "v0.2 release created",
        "implementation approval set true",
        "backlog implementation item approved",
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
        "approval workflow bypassed",
        "ADR dependency bypassed",
        "gate dependency bypassed",
    ]:
        assert condition in no_go

    adr = _text("docs/adr/0113-v02-implementation-kickoff-boundary.md")
    assert "Decision: add v0.2 implementation kickoff boundary." in adr
    assert "Decision: AION-122 does not approve implementation." in adr
    assert "Decision: v0.2 remains planning-only after AION-122." in adr
    assert "Decision: future implementation requires explicit approval workflow, ADRs, and" in adr
    assert "Decision: no v0.2 release or tag is created." in adr
    assert "Reason: AION needs an implementation request and approval boundary before" in adr
    assert "Consequence: implementation tasks cannot begin without explicit approval" in adr
    assert "Constraint: no runtime enablement." in adr
    assert "Constraint: no external calls." in adr
    assert "Constraint: no credentials/tokens." in adr
    assert "Constraint: no sandbox execution." in adr
    assert "Constraint: no privileged bypass." in adr


def test_v02_implementation_kickoff_examples_are_safe() -> None:
    for relative in EXAMPLES:
        payload = _json(relative)
        if relative.startswith("examples/"):
            assert payload["synthetic"] is True
        assert payload["status"] == "passed"
        assert payload["task_id"] == "AION-122"
        assert payload["v02_implementation_kickoff_boundary_created"] is True
        _assert_false_keys(payload, relative)


def test_v02_implementation_kickoff_scripts_are_executable_and_pass() -> None:
    for script in [
        ROOT / "scripts/v02-implementation-kickoff-boundary-check.sh",
        ROOT / "scripts/v02-implementation-kickoff-freeze.sh",
        ROOT / "scripts/v02-implementation-kickoff-no-go-regression.sh",
    ]:
        assert script.exists()
        assert script.stat().st_mode & stat.S_IXUSR

    env = os.environ.copy()
    env["AION_V02_IMPLEMENTATION_KICKOFF_SKIP_NESTED_GATES"] = "1"
    env["AION_V02_IMPLEMENTATION_KICKOFF_FREEZE_SKIP_FULL_CHECK"] = "1"
    subprocess.run(
        ["./scripts/v02-implementation-kickoff-boundary-check.sh"],
        cwd=ROOT,
        env=env,
        check=True,
    )
    subprocess.run(
        ["./scripts/v02-implementation-kickoff-freeze.sh"],
        cwd=ROOT,
        env=env,
        check=True,
    )
    subprocess.run(
        ["./scripts/v02-implementation-kickoff-no-go-regression.sh"],
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
