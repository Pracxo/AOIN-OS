"""AION-128 v0.2 planning master checkpoint regression tests."""

from __future__ import annotations

import json
import os
import stat
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]

DOCS = [
    "docs/release/v02-planning-master-checkpoint.md",
    "docs/release/v02-proposal-governance-baseline.md",
    "docs/release/v02-implementation-lock-freeze.md",
    "docs/release/v02-approval-queue-baseline-summary.md",
    "docs/release/v02-planning-master-evidence-matrix.md",
    "docs/release/v02-planning-master-no-go.md",
    "docs/release/v02-planning-master-closeout-checklist.md",
    "docs/release/v02-planning-master-summary.md",
    "docs/adr/0119-v02-planning-master-checkpoint.md",
]

EXAMPLES = [
    "examples/release/v02-planning-master-checkpoint.json",
    "examples/release/v02-proposal-governance-baseline.json",
    "examples/release/v02-implementation-lock-freeze.json",
    "examples/release/v02-approval-queue-baseline-summary.json",
    "examples/release/v02-planning-master-evidence-matrix.json",
    "operator-console-static/demo-data/v02-planning-master-checkpoint.json",
    "operator-console-static/demo-data/v02-implementation-lock-freeze.json",
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


def test_v02_planning_master_docs_exist_and_are_indexed() -> None:
    for relative in DOCS:
        assert (ROOT / relative).exists(), relative

    index = _text("docs/adr/README.md")
    assert "0119-v02-planning-master-checkpoint.md" in index

    checkpoint = _text("docs/release/v02-planning-master-checkpoint.md")
    for heading in [
        "## Purpose",
        "## Scope",
        "## AION-119 Through AION-127 Summary",
        "## Planning Charter Baseline",
        "## Approval Workflow Baseline",
        "## Workstream Intake Baseline",
        "## Proposal Registry Baseline",
        "## Approval Queue Baseline",
        "## Implementation Lock State",
        "## No-Go Conditions",
        "## No v0.2 Tag Or Release",
    ]:
        assert heading in checkpoint
    assert "AION-128 explicitly creates no v0.2 tag and no release" in checkpoint

    governance = _text("docs/release/v02-proposal-governance-baseline.md")
    for required in [
        "proposal registry remains preview-only",
        "approval queue remains preview-only",
        "Proposal implementation approval remains false",
        "Approval queue item approval remains false",
        "## Required ADR Dependency",
        "## Required Gate Dependency",
        "## Required Security Review",
        "## Required Architecture Review",
        "## Required Operator Review",
        "## Required Rollback And Audit Evidence",
        "## No Direct Implementation Approval",
    ]:
        assert required in governance

    lock = _text("docs/release/v02-implementation-lock-freeze.md")
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
        assert required in lock

    queue = _text("docs/release/v02-approval-queue-baseline-summary.md")
    for required in [
        "## Queue Purpose",
        "## Preview-Only Status",
        "Queue placement does not approve implementation.",
        "The queue cannot enable runtime",
        "Every queue item keeps `approval_queue_item_approved=false`.",
        "## Required Reviewers",
        "## Expiry And Revocation Requirements",
        "## Dual-Control Requirements",
        "## No-Go Conditions",
    ]:
        assert required in queue

    matrix = _text("docs/release/v02-planning-master-evidence-matrix.md")
    for required in [
        "Area",
        "Evidence source",
        "Gate script",
        "Expected safe value",
        "Approval state",
        "Release blocker if violated",
        "Notes",
    ]:
        assert required in matrix

    no_go = _text("docs/release/v02-planning-master-no-go.md")
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

    checklist = _text("docs/release/v02-planning-master-closeout-checklist.md")
    for required in [
        "docs complete",
        "examples valid",
        "scripts executable",
        "proposal registry stabilization passing",
        "preimplementation master freeze passing",
        "workstream intake readiness passing",
        "approval workflow stabilization passing",
        "readiness final review passing",
        "planning stabilization passing",
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

    adr = _text("docs/adr/0119-v02-planning-master-checkpoint.md")
    for required in [
        "Decision: add v0.2 planning master checkpoint.",
        "Decision: AION-128 does not approve implementation.",
        "Decision: v0.2 remains planning-only after AION-128.",
        "Decision: proposal registry and approval queue remain preview-only.",
        "Decision: all implementation approval states remain false.",
        "Decision: no v0.2 release or tag is created.",
        (
            "Reason: AION needs a single final planning checkpoint before any "
            "implementation proposal can be considered."
        ),
        (
            "Consequence: future runtime work must begin from this frozen "
            "planning governance baseline."
        ),
        "Constraint: no runtime enablement.",
        "Constraint: no external calls.",
        "Constraint: no credentials/tokens.",
        "Constraint: no sandbox execution.",
        "Constraint: no privileged bypass.",
    ]:
        assert required in adr


def test_v02_planning_master_examples_are_safe() -> None:
    for relative in EXAMPLES:
        payload = _json(relative)
        assert payload["task_id"] == "AION-128"
        assert payload["status"] == "passed"
        assert payload["synthetic"] is True
        assert payload["v02_planning_master_checkpoint_passed"] is True
        assert payload["proposal_registry_preview_only"] is True
        assert payload["approval_queue_preview_only"] is True
        _assert_false_keys(payload, relative)

    matrix = _json("examples/release/v02-planning-master-evidence-matrix.json")
    for item in matrix["matrix"]:
        assert item["area"]
        assert item["evidence_source"]
        assert item["gate_script"].startswith("./scripts/")
        assert item["expected_safe_value"]
        assert item["approval_state"] is False
        assert item["release_blocker_if_violated"] is True


def test_v02_planning_master_scripts_are_executable_and_pass() -> None:
    scripts = [
        ROOT / "scripts/v02-planning-master-checkpoint.sh",
        ROOT / "scripts/v02-planning-master-freeze.sh",
        ROOT / "scripts/v02-planning-master-no-go-regression.sh",
    ]
    for script in scripts:
        assert script.exists()
        assert os.access(script, os.X_OK)
        assert script.stat().st_mode & stat.S_IXUSR
        subprocess.run(["bash", "-n", str(script)], cwd=ROOT, check=True)

    env = os.environ.copy()
    env["AION_V02_PLANNING_MASTER_CHECKPOINT_SKIP_INHERITED_GATES"] = "1"
    env["AION_V02_PLANNING_MASTER_FREEZE_SKIP_FULL_CHECK"] = "1"
    subprocess.run(
        ["./scripts/v02-planning-master-no-go-regression.sh"],
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
