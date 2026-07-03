"""AION-129 v0.2 final planning release gate regression tests."""

from __future__ import annotations

import json
import os
import stat
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]

DOCS = [
    "docs/release/v02-final-planning-release-gate.md",
    "docs/release/v02-governance-baseline-evidence.md",
    "docs/release/v02-no-implementation-freeze.md",
    "docs/release/v02-final-approval-lock-evidence.md",
    "docs/release/v02-planning-release-gate-matrix.md",
    "docs/release/v02-final-planning-no-go.md",
    "docs/release/v02-final-planning-release-checklist.md",
    "docs/adr/0120-v02-final-planning-release-gate.md",
]

EXAMPLES = [
    "examples/release/v02-final-planning-release-gate.json",
    "examples/release/v02-governance-baseline-evidence.json",
    "examples/release/v02-no-implementation-freeze.json",
    "examples/release/v02-final-approval-lock-evidence.json",
    "examples/release/v02-planning-release-gate-matrix.json",
    "operator-console-static/demo-data/v02-final-planning-release-gate.json",
    "operator-console-static/demo-data/v02-no-implementation-freeze.json",
]

FALSE_KEYS = {
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
    "approval_expiry_bypassed",
    "approval_revocation_bypassed",
    "dual_control_bypassed",
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
    "api_runtime_execution_route_added",
    "sdk_resource_implementation_added",
    "cli_command_implementation_added",
    "frontend_dependencies_added",
    "secrets_present",
    "tokens_present",
    "credentials_present",
    "credential_values_present",
    "token_values_present",
    "endpoints_present",
    "prompt_payloads_present",
    "private_reasoning_present",
}


def test_v02_final_planning_docs_exist_and_are_indexed() -> None:
    for relative in DOCS:
        assert (ROOT / relative).exists(), relative

    index = _text("docs/adr/README.md")
    assert "0120-v02-final-planning-release-gate.md" in index

    gate = _text("docs/release/v02-final-planning-release-gate.md")
    for heading in [
        "## Purpose",
        "## Scope",
        "## Required Prior Gates",
        "## AION-119 Through AION-128 Summary",
        "## Governance Baseline Evidence",
        "## Proposal Registry Evidence",
        "## Approval Queue Evidence",
        "## Implementation Lock Evidence",
        "## Release Blocker Conditions",
        "## Pass/Fail Criteria",
        "## No v0.2 Tag Or Release",
    ]:
        assert heading in gate
    assert "AION-129 explicitly creates no v0.2 tag and no v0.2 release" in gate

    governance = _text("docs/release/v02-governance-baseline-evidence.md")
    for required in [
        "v0.2 planning charter",
        "Planning stabilization",
        "Readiness final review",
        "Implementation kickoff boundary",
        "Approval workflow stabilization",
        "Workstream intake readiness",
        "Preimplementation master freeze",
        "Proposal registry",
        "Proposal registry stabilization",
        "Planning master checkpoint",
        "Docs and boundary checks",
    ]:
        assert required in governance

    freeze = _text("docs/release/v02-no-implementation-freeze.md")
    for required in [
        "runtime_implementation_approved=false",
        "backlog_implementation_items_approved=false",
        "workstream_implementation_approved=false",
        "proposal_implementation_approved=false",
        "approval_queue_item_approved=false",
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
        assert required in freeze

    approval_lock = _text("docs/release/v02-final-approval-lock-evidence.md")
    for required in [
        "approval workflow bypass false",
        "approval record missing false",
        "ADR dependency bypass false",
        "gate dependency bypass false",
        "approval expiry bypass false",
        "approval revocation bypass false",
        "dual-control bypass false",
        "approval queue item approval false",
        "proposal implementation approval false",
    ]:
        assert required in approval_lock

    matrix = _text("docs/release/v02-planning-release-gate-matrix.md")
    for required in [
        "Area",
        "Required gate",
        "Required evidence",
        "Expected safe state",
        "Approval state",
        "Release blocker if violated",
        "Notes",
    ]:
        assert required in matrix

    no_go = _text("docs/release/v02-final-planning-no-go.md")
    for condition in [
        "v0.2 tag created",
        "v0.2 release created",
        "runtime implementation approval true",
        "backlog implementation approval true",
        "workstream implementation approval true",
        "proposal implementation approval true",
        "approval queue item approved true",
        "approval workflow bypassed",
        "approval record missing",
        "ADR dependency bypassed",
        "gate dependency bypassed",
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

    checklist = _text("docs/release/v02-final-planning-release-checklist.md")
    for required in [
        "docs complete",
        "examples valid",
        "scripts executable",
        "planning master checkpoint passing",
        "proposal registry stabilization passing",
        "preimplementation master freeze passing",
        "approval workflow stabilization passing",
        "workstream intake readiness passing",
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

    adr = _text("docs/adr/0120-v02-final-planning-release-gate.md")
    for required in [
        "Decision: add v0.2 final planning release gate.",
        "Decision: AION-129 does not approve implementation.",
        "Decision: v0.2 remains planning-only after AION-129.",
        "Decision: proposal registry and approval queue remain preview-only.",
        "Decision: all implementation approval states remain false.",
        "Decision: no v0.2 release or tag is created.",
        (
            "Reason: AION needs a final release-grade planning gate before any "
            "runtime implementation proposal can proceed."
        ),
        (
            "Consequence: future implementation must begin from this frozen "
            "planning release-gate baseline."
        ),
        "Constraint: no runtime enablement.",
        "Constraint: no external calls.",
        "Constraint: no credentials/tokens.",
        "Constraint: no sandbox execution.",
        "Constraint: no privileged bypass.",
    ]:
        assert required in adr


def test_v02_final_planning_examples_are_safe() -> None:
    for relative in EXAMPLES:
        payload = _json(relative)
        assert payload["task_id"] == "AION-129"
        assert payload["status"] == "passed"
        assert payload["synthetic"] is True
        assert payload["v02_final_planning_release_gate_passed"] is True
        assert payload["proposal_registry_preview_only"] is True
        assert payload["approval_queue_preview_only"] is True
        _assert_false_keys(payload, relative)

    matrix = _json("examples/release/v02-planning-release-gate-matrix.json")
    for item in matrix["matrix"]:
        assert item["area"]
        assert item["required_gate"].startswith("./scripts/")
        assert item["required_evidence"]
        assert item["expected_safe_state"]
        assert item["approval_state"] is False
        assert item["release_blocker_if_violated"] is True


def test_v02_final_planning_scripts_are_executable_and_pass() -> None:
    scripts = [
        ROOT / "scripts/v02-final-planning-release-gate.sh",
        ROOT / "scripts/v02-final-planning-freeze.sh",
        ROOT / "scripts/v02-final-planning-no-go-regression.sh",
    ]
    for script in scripts:
        assert script.exists()
        assert os.access(script, os.X_OK)
        assert script.stat().st_mode & stat.S_IXUSR
        subprocess.run(["bash", "-n", str(script)], cwd=ROOT, check=True)

    env = os.environ.copy()
    env["AION_V02_FINAL_PLANNING_RELEASE_GATE_SKIP_INHERITED_GATES"] = "1"
    env["AION_V02_FINAL_PLANNING_FREEZE_SKIP_FULL_CHECK"] = "1"
    subprocess.run(
        ["./scripts/v02-final-planning-no-go-regression.sh"],
        cwd=ROOT,
        env=env,
        check=True,
    )


def _text(relative: str) -> str:
    return (ROOT / relative).read_text()


def _json(relative: str) -> dict[str, Any]:
    return json.loads((ROOT / relative).read_text())


def _assert_false_keys(value: Any, context: str) -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            if key in FALSE_KEYS:
                assert nested is False, f"{context}.{key} must be false"
            if key in {"implementation_approved", "approval_state"}:
                assert nested is False, f"{context}.{key} must be false"
            _assert_false_keys(nested, f"{context}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _assert_false_keys(item, f"{context}[{index}]")
