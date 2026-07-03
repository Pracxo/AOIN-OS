"""AION-127 v0.2 proposal registry stabilization regression tests."""

from __future__ import annotations

import json
import os
import stat
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]

DOCS = [
    "docs/release/v02-proposal-registry-stabilization-gate.md",
    "docs/release/v02-approval-queue-freeze.md",
    "docs/release/v02-candidate-workstream-evidence-baseline.md",
    "docs/release/v02-proposal-lifecycle-evidence-matrix.md",
    "docs/release/v02-proposal-registry-closeout-checklist.md",
    "docs/release/v02-approval-queue-no-go.md",
    "docs/release/v02-proposal-registry-stabilization-summary.md",
    "docs/adr/0118-v02-proposal-registry-stabilization.md",
]

EXAMPLES = [
    "examples/release/v02-proposal-registry-stabilization-gate.json",
    "examples/release/v02-approval-queue-freeze.json",
    "examples/release/v02-candidate-workstream-evidence-baseline.json",
    "examples/release/v02-proposal-lifecycle-evidence-matrix.json",
    "examples/release/v02-proposal-registry-closeout-result.json",
    "operator-console-static/demo-data/v02-proposal-registry-stabilization.json",
    "operator-console-static/demo-data/v02-approval-queue-freeze.json",
]

FALSE_KEYS = {
    "approval_queue_item_approved",
    "proposal_implementation_approved",
    "v02_tag_created",
    "v02_release_created",
    "v02_release_approved",
    "runtime_implementation_approved",
    "backlog_implementation_items_approved",
    "workstream_implementation_approved",
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
    "credential_values_present",
    "token_values_present",
    "endpoints_present",
    "prompt_payloads_present",
    "private_reasoning_present",
}

WORKSTREAMS = {
    "production auth implementation proposal",
    "audit/provenance hardening proposal",
    "rollback/recovery proposal",
    "external call release gate proposal",
    "connector runtime implementation proposal",
    "credential store implementation proposal",
    "sandbox runtime implementation proposal",
    "operator write execution proposal",
    "module activation proposal",
    "production UI decision proposal",
}


def test_v02_proposal_registry_stabilization_docs_exist_and_are_indexed() -> None:
    for relative in DOCS:
        assert (ROOT / relative).exists(), relative

    index = _text("docs/adr/README.md")
    assert "0118-v02-proposal-registry-stabilization.md" in index

    gate = _text("docs/release/v02-proposal-registry-stabilization-gate.md")
    for heading in [
        "## Purpose",
        "## Scope",
        "## Required Prior Gates",
        "## Proposal Registry Evidence",
        "## Approval Queue Evidence",
        "## Candidate Workstream Evidence",
        "## Lifecycle Evidence",
        "## Approval Lock Checks",
        "## No-Go Conditions",
        "## No v0.2 Tag Or Release",
    ]:
        assert heading in gate
    assert "AION-127 explicitly creates no v0.2 tag and no release" in gate

    queue = _text("docs/release/v02-approval-queue-freeze.md")
    for required in [
        "## Queue Remains Preview-Only",
        "## Queue Does Not Approve Implementation",
        "## Queue Does Not Enable Runtime",
        "## Queue Item Approval Remains False",
        "## Required Reviewers",
        "## Required Evidence",
        "## Expiry And Revocation Rules",
        "## ADR Dependency Rule",
        "## Gate Dependency Rule",
        "## No-Go Conditions",
    ]:
        assert required in queue

    candidate = _text("docs/release/v02-candidate-workstream-evidence-baseline.md")
    for workstream in WORKSTREAMS:
        assert workstream in candidate
    for required in [
        "Proposal status",
        "Approval status false",
        "Implementation status false",
        "Required ADR",
        "Required gate",
        "Required evidence",
        "Blocker",
        "Next planning action",
    ]:
        assert required in candidate

    matrix = _text("docs/release/v02-proposal-lifecycle-evidence-matrix.md")
    for required in [
        "Proposal state",
        "Required evidence",
        "Required reviewer",
        "Allowed today",
        "Implementation approved",
        "Runtime enabled",
        "Release blocker if violated",
        "Notes",
        "All implementation approved and runtime enabled values remain false.",
    ]:
        assert required in matrix

    checklist = _text("docs/release/v02-proposal-registry-closeout-checklist.md")
    for required in [
        "docs complete",
        "examples valid",
        "scripts executable",
        "proposal registry check passing",
        "proposal registry freeze passing",
        "approval queue no-go regression passing",
        "preimplementation master freeze passing",
        "workstream intake readiness passing",
        "approval workflow stabilization passing",
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

    no_go = _text("docs/release/v02-approval-queue-no-go.md")
    for condition in [
        "approval queue item approved true",
        "proposal state implies implementation approved",
        "implementation approval set true",
        "workstream implementation approval set true",
        "backlog implementation approval set true",
        "approval workflow bypassed",
        "approval record missing",
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

    summary = _text("docs/release/v02-proposal-registry-stabilization-summary.md")
    for required in [
        "proposal_registry_stabilized=true",
        "proposal_registry_preview_only=true",
        "approval_queue_preview_only=true",
        "approval_queue_item_approved=false",
        "proposal_implementation_approved=false",
        "runtime_implementation_approved=false",
        "workstream_implementation_approved=false",
        "v02_tag_created=false",
        "v02_release_created=false",
    ]:
        assert required in summary

    adr = _text("docs/adr/0118-v02-proposal-registry-stabilization.md")
    for required in [
        "Decision: add v0.2 proposal registry stabilization gate.",
        "Decision: AION-127 does not approve implementation.",
        "Decision: proposal registry and approval queue remain preview-only.",
        "Decision: approval queue item approval remains false.",
        (
            "Decision: future implementation still requires explicit approval "
            "records, ADRs, and gate evidence."
        ),
        "Decision: no v0.2 release or tag is created.",
        (
            "Reason: AION needs a stable proposal and approval queue baseline "
            "before implementation approval can be considered."
        ),
        (
            "Consequence: future workstreams remain blocked until explicit "
            "approval records are created."
        ),
        "Constraint: no runtime enablement.",
        "Constraint: no external calls.",
        "Constraint: no credentials/tokens.",
        "Constraint: no sandbox execution.",
        "Constraint: no privileged bypass.",
    ]:
        assert required in adr


def test_v02_proposal_registry_stabilization_examples_are_safe() -> None:
    for relative in EXAMPLES:
        payload = _json(relative)
        assert payload["task_id"] == "AION-127"
        assert payload["status"] == "passed"
        assert payload["synthetic"] is True
        assert payload["v02_proposal_registry_stabilized"] is True
        assert payload["proposal_registry_preview_only"] is True
        assert payload["approval_queue_preview_only"] is True
        _assert_false_keys(payload, relative)

    candidate = _json("examples/release/v02-candidate-workstream-evidence-baseline.json")
    assert {item["proposal"] for item in candidate["workstreams"]} == WORKSTREAMS
    for item in candidate["workstreams"]:
        assert item["approval_status"] is False
        assert item["implementation_status"] is False
        assert item["required_adr"]
        assert item["required_gate"]
        assert item["required_evidence"]
        assert item["blocker"]
        assert item["next_planning_action"]

    matrix = _json("examples/release/v02-proposal-lifecycle-evidence-matrix.json")
    for item in matrix["matrix"]:
        assert item["implementation_approved"] is False
        assert item["runtime_enabled"] is False


def test_v02_proposal_registry_stabilization_scripts_are_executable_and_pass() -> None:
    scripts = [
        ROOT / "scripts/v02-proposal-registry-stabilization-gate.sh",
        ROOT / "scripts/v02-approval-queue-freeze.sh",
        ROOT / "scripts/v02-approval-queue-no-go-regression.sh",
    ]
    for script in scripts:
        assert script.exists()
        assert os.access(script, os.X_OK)
        assert script.stat().st_mode & stat.S_IXUSR
        subprocess.run(["bash", "-n", str(script)], cwd=ROOT, check=True)

    env = os.environ.copy()
    env["AION_V02_PROPOSAL_REGISTRY_STABILIZATION_SKIP_INHERITED_GATES"] = "1"
    env["AION_V02_APPROVAL_QUEUE_FREEZE_SKIP_FULL_CHECK"] = "1"
    subprocess.run(
        ["./scripts/v02-approval-queue-no-go-regression.sh"],
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
            if key in {
                "implementation_approved",
                "approval_status",
                "implementation_status",
                "runtime_enabled",
            }:
                assert nested is False, f"{context}.{key} must be false"
            _assert_false_keys(nested, f"{context}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _assert_false_keys(item, f"{context}[{index}]")
