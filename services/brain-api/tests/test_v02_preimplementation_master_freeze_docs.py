"""AION-125 v0.2 pre-implementation master freeze regression tests."""

from __future__ import annotations

import json
import os
import stat
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]

DOCS = [
    "docs/release/v02-preimplementation-master-freeze.md",
    "docs/release/v02-final-planning-baseline.md",
    "docs/release/v02-workstream-governance-closeout.md",
    "docs/release/v02-approval-workflow-closeout-evidence.md",
    "docs/release/v02-implementation-lock-summary.md",
    "docs/release/v02-master-no-go-regression.md",
    "docs/release/v02-preimplementation-final-checklist.md",
    "docs/adr/0116-v02-preimplementation-master-freeze.md",
]

EXAMPLES = [
    "examples/release/v02-preimplementation-master-freeze.json",
    "examples/release/v02-final-planning-baseline.json",
    "examples/release/v02-workstream-governance-closeout.json",
    "examples/release/v02-approval-workflow-closeout-evidence.json",
    "examples/release/v02-implementation-lock-summary.json",
    "operator-console-static/demo-data/v02-preimplementation-master-freeze.json",
    "operator-console-static/demo-data/v02-final-planning-baseline.json",
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
    "workstream_implementation_approved",
    "approval_workflow_bypassed",
    "approval_record_missing",
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


def test_v02_preimplementation_docs_exist_and_are_indexed() -> None:
    for relative in DOCS:
        assert (ROOT / relative).exists(), relative

    index = _text("docs/adr/README.md")
    assert "0116-v02-preimplementation-master-freeze.md" in index

    freeze = _text("docs/release/v02-preimplementation-master-freeze.md")
    for heading in [
        "## Purpose",
        "## Scope",
        "## Required Prior Gates",
        "## Planning Charter Status",
        "## Planning Stabilization Status",
        "## Readiness Final Review Status",
        "## Kickoff Boundary Status",
        "## Approval Workflow Status",
        "## Workstream Intake Status",
        "## Implementation Lock Status",
        "## No-Go Conditions",
        "## No v0.2 Tag Or Release",
    ]:
        assert heading in freeze
    assert "AION-125 explicitly creates no v0.2 tag and no release" in freeze

    baseline = _text("docs/release/v02-final-planning-baseline.md")
    for heading in [
        "## Completed Planning Artifacts",
        "## Completed Approval Artifacts",
        "## Completed Workstream Intake Artifacts",
        "## Completed No-Go Regressions",
        "## Current Implementation Approval State",
        "## Current Runtime Safe State",
        "## Required Future ADRs",
        "## Required Future Release Gates",
        "## Final Planning Baseline Decision",
    ]:
        assert heading in baseline

    governance = _text("docs/release/v02-workstream-governance-closeout.md")
    for heading in [
        "## Workstream Intake Boundary",
        "## Approval Record Requirement",
        "## ADR Dependency Requirement",
        "## Gate Dependency Requirement",
        "## Security Review Requirement",
        "## Architecture Review Requirement",
        "## Operator Review Requirement",
        "## Rollback/Audit Requirement",
        "## Rejection Rules",
        "## Closeout Decision",
    ]:
        assert heading in governance

    approval = _text("docs/release/v02-approval-workflow-closeout-evidence.md")
    for required in [
        "## Approval Workflow Blueprint Evidence",
        "## Intake Validation Evidence",
        "## Approval Decision Evidence",
        "## Expiry Model Evidence",
        "## Revocation Model Evidence",
        "## Dual-Control Evidence",
        "## No-Go Regression Evidence",
        "## Approval Remains False",
    ]:
        assert required in approval

    lock = _text("docs/release/v02-implementation-lock-summary.md")
    for required in [
        "runtime_implementation_approved=false",
        "backlog_implementation_items_approved=false",
        "workstream_implementation_approved=false",
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
        assert required in lock

    no_go = _text("docs/release/v02-master-no-go-regression.md")
    for condition in [
        "v0.2 tag created",
        "v0.2 release created",
        "runtime implementation approval true",
        "backlog implementation approval true",
        "workstream implementation approval true",
        "approval workflow bypassed",
        "approval record missing",
        "ADR dependency bypassed",
        "gate dependency bypassed",
        "approval expiry bypassed",
        "approval revocation bypassed",
        "dual-control bypassed",
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

    checklist = _text("docs/release/v02-preimplementation-final-checklist.md")
    for item in [
        "docs complete",
        "examples valid",
        "scripts executable",
        "v0.2 planning charter passing",
        "planning stabilization passing",
        "readiness final review passing",
        "implementation kickoff boundary passing",
        "approval workflow stabilization passing",
        "workstream intake readiness passing",
        "no-go regressions passing",
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

    adr = _text("docs/adr/0116-v02-preimplementation-master-freeze.md")
    assert "Decision: add v0.2 pre-implementation master freeze." in adr
    assert "Decision: AION-125 does not approve implementation." in adr
    assert "Decision: v0.2 remains planning-only after AION-125." in adr
    assert "Decision: all implementation approval states remain false." in adr
    assert "Decision: future implementation requires explicit approval records, ADRs," in adr
    assert "Decision: no v0.2 release or tag is created." in adr
    assert "Reason: AION needs a final master freeze before any implementation" in adr
    assert "Consequence: future runtime work must start from this frozen planning baseline." in adr
    assert "Constraint: no runtime enablement." in adr
    assert "Constraint: no external calls." in adr
    assert "Constraint: no credentials/tokens." in adr
    assert "Constraint: no sandbox execution." in adr
    assert "Constraint: no privileged bypass." in adr


def test_v02_preimplementation_examples_are_safe() -> None:
    for relative in EXAMPLES:
        payload = _json(relative)
        if relative.startswith("examples/"):
            assert payload["synthetic"] is True
        assert payload["status"] == "passed"
        assert payload["task_id"] == "AION-125"
        assert payload["v02_preimplementation_master_freeze_passed"] is True
        _assert_false_keys(payload, relative)


def test_v02_preimplementation_scripts_are_executable_and_pass() -> None:
    for script in [
        ROOT / "scripts/v02-preimplementation-master-freeze.sh",
        ROOT / "scripts/v02-preimplementation-final-baseline-check.sh",
        ROOT / "scripts/v02-preimplementation-master-no-go-regression.sh",
    ]:
        assert script.exists()
        assert os.access(script, os.X_OK)
        assert script.stat().st_mode & stat.S_IXUSR

    env = os.environ.copy()
    env["AION_V02_PREIMPLEMENTATION_MASTER_SKIP_NESTED_GATES"] = "1"
    env["AION_V02_PREIMPLEMENTATION_BASELINE_SKIP_FULL_CHECK"] = "1"
    subprocess.run(
        ["./scripts/v02-preimplementation-master-freeze.sh"],
        cwd=ROOT,
        env=env,
        check=True,
    )
    subprocess.run(
        ["./scripts/v02-preimplementation-final-baseline-check.sh"],
        cwd=ROOT,
        env=env,
        check=True,
    )
    subprocess.run(
        ["./scripts/v02-preimplementation-master-no-go-regression.sh"],
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
