"""AION-130 v0.2 planning track closeout regression tests."""

from __future__ import annotations

import json
import os
import stat
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]

DOCS = [
    "docs/release/v02-planning-track-closeout-report.md",
    "docs/release/v02-governance-handoff-pack.md",
    "docs/release/v02-implementation-request-phase-boundary.md",
    "docs/release/v02-final-approval-state-ledger.md",
    "docs/release/v02-final-proposal-queue-status-summary.md",
    "docs/release/v02-planning-track-evidence-index.md",
    "docs/release/v02-planning-track-closeout-no-go.md",
    "docs/adr/0121-v02-planning-track-closeout.md",
]

EXAMPLES = [
    "examples/release/v02-planning-track-closeout-report.json",
    "examples/release/v02-governance-handoff-pack.json",
    "examples/release/v02-implementation-request-phase-boundary.json",
    "examples/release/v02-final-approval-state-ledger.json",
    "examples/release/v02-final-proposal-queue-status-summary.json",
    "operator-console-static/demo-data/v02-planning-track-closeout.json",
    "operator-console-static/demo-data/v02-governance-handoff-pack.json",
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


def test_v02_planning_track_closeout_docs_exist_and_are_indexed() -> None:
    for relative in DOCS:
        assert (ROOT / relative).exists(), relative

    index = _text("docs/adr/README.md")
    assert "0121-v02-planning-track-closeout.md" in index

    closeout = _text("docs/release/v02-planning-track-closeout-report.md")
    for heading in [
        "## Purpose",
        "## Scope",
        "## AION-119 Through AION-129 Summary",
        "## Planning Artifacts Completed",
        "## Governance Artifacts Completed",
        "## Proposal Registry Artifacts Completed",
        "## Approval Queue Artifacts Completed",
        "## Final Planning Release Gate Status",
        "## Implementation Approval State",
        "## Closeout Decision",
        "## No v0.2 Tag Or Release",
    ]:
        assert heading in closeout
    assert "AION-130 explicitly creates no v0.2 tag and no v0.2 release" in closeout

    handoff = _text("docs/release/v02-governance-handoff-pack.md")
    for heading in [
        "## What Is Handed Off",
        "## What Remains Blocked",
        "## Required Future Approval Records",
        "## Required Future ADRs",
        "## Required Future Gates",
        "## Required Security Review",
        "## Required Architecture Review",
        "## Required Operator Review",
        "## Required Rollback/Audit Evidence",
        "## No-Go Conditions",
        "## Handoff Decision",
    ]:
        assert heading in handoff

    boundary = _text("docs/release/v02-implementation-request-phase-boundary.md")
    for required in [
        "implementation requests may be proposed only through the proposal registry",
        "The proposal registry remains preview-only",
        "The approval queue remains preview-only",
        "approval_queue_item_approved=false",
        "proposal_implementation_approved=false",
        "runtime_implementation_approved=false",
        "No runtime capability is enabled",
        "Future implementation requires explicit approval records, ADRs, and gate evidence",
    ]:
        assert required in boundary

    ledger = _text("docs/release/v02-final-approval-state-ledger.md")
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
        assert required in ledger

    queue = _text("docs/release/v02-final-proposal-queue-status-summary.md")
    for required in [
        "proposal registry remains preview-only",
        "approval queue remains preview-only",
        "Candidate workstreams",
        "Approval status",
        "Implementation status",
        "Future movement requires a proposal record, approval record, ADR, gate evidence",
        "No-Go Conditions",
    ]:
        assert required in queue

    evidence_index = _text("docs/release/v02-planning-track-evidence-index.md")
    for required in [
        "v0.2 planning charter",
        "planning stabilization",
        "readiness final review",
        "implementation kickoff boundary",
        "approval workflow stabilization",
        "workstream intake readiness",
        "preimplementation master freeze",
        "proposal registry",
        "proposal registry stabilization",
        "planning master checkpoint",
        "final planning release gate",
        "Document",
        "ADR",
        "Script",
        "Example evidence",
        "Expected safe state",
        "Release blocker",
    ]:
        assert required in evidence_index

    no_go = _text("docs/release/v02-planning-track-closeout-no-go.md")
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

    adr = _text("docs/adr/0121-v02-planning-track-closeout.md")
    for required in [
        "Decision: add v0.2 planning track closeout.",
        "Decision: AION-130 does not approve implementation.",
        "Decision: v0.2 remains planning-only after AION-130.",
        "Decision: proposal registry and approval queue remain preview-only.",
        "Decision: all implementation approval states remain false.",
        "Decision: no v0.2 release or tag is created.",
        (
            "Reason: AION needs a complete governance handoff baseline before "
            "implementation requests can be considered."
        ),
        (
            "Consequence: future runtime work must begin from the frozen "
            "planning track closeout."
        ),
        "Constraint: no runtime enablement.",
        "Constraint: no external calls.",
        "Constraint: no credentials/tokens.",
        "Constraint: no sandbox execution.",
        "Constraint: no privileged bypass.",
    ]:
        assert required in adr


def test_v02_planning_track_closeout_examples_are_safe() -> None:
    for relative in EXAMPLES:
        payload = _json(relative)
        assert payload["task_id"] == "AION-130"
        assert payload["status"] == "passed"
        assert payload["synthetic"] is True
        assert payload["v02_planning_track_closeout_passed"] is True
        assert payload["governance_handoff_ready"] is True
        assert payload["implementation_request_phase_boundary_created"] is True
        assert payload["proposal_registry_preview_only"] is True
        assert payload["approval_queue_preview_only"] is True
        _assert_false_keys(payload, relative)

    for relative in EXAMPLES[-2:]:
        payload = _json(relative)
        assert payload["read_only"] is True
        assert payload["redaction_applied"] is True
        assert payload["sections"]
        assert payload["blockers"]
        assert payload["warnings"]
        assert payload["refs"]
        assert payload["forbidden_actions"]


def test_v02_planning_track_closeout_scripts_are_executable_and_pass() -> None:
    scripts = [
        ROOT / "scripts/v02-planning-track-closeout.sh",
        ROOT / "scripts/v02-planning-track-handoff-freeze.sh",
        ROOT / "scripts/v02-planning-track-closeout-no-go-regression.sh",
    ]
    for script in scripts:
        assert script.exists()
        assert os.access(script, os.X_OK)
        assert script.stat().st_mode & stat.S_IXUSR
        subprocess.run(["bash", "-n", str(script)], cwd=ROOT, check=True)

    env = os.environ.copy()
    env["AION_V02_PLANNING_TRACK_CLOSEOUT_SKIP_INHERITED_GATES"] = "1"
    env["AION_V02_PLANNING_TRACK_HANDOFF_FREEZE_SKIP_FULL_CHECK"] = "1"
    subprocess.run(
        ["./scripts/v02-planning-track-closeout-no-go-regression.sh"],
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
