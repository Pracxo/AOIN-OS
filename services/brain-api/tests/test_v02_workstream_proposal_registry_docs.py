"""AION-126 v0.2 workstream proposal registry regression tests."""

from __future__ import annotations

import json
import os
import stat
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]

DOCS = [
    "docs/release/v02-workstream-proposal-registry.md",
    "docs/release/v02-implementation-request-index.md",
    "docs/release/v02-approval-queue-preview.md",
    "docs/release/v02-proposal-review-rules.md",
    "docs/release/v02-proposal-state-machine.md",
    "docs/release/v02-proposal-evidence-requirements.md",
    "docs/release/v02-proposal-registry-no-go.md",
    "docs/adr/0117-v02-workstream-proposal-registry.md",
]

EXAMPLES = [
    "examples/release/v02-workstream-proposal-registry.json",
    "examples/release/v02-implementation-request-index.json",
    "examples/release/v02-approval-queue-preview.json",
    "examples/release/v02-proposal-state-machine.json",
    "examples/release/v02-proposal-evidence-requirements.json",
    "operator-console-static/demo-data/v02-workstream-proposal-registry.json",
    "operator-console-static/demo-data/v02-approval-queue-preview.json",
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
    "approval_queue_item_approved",
    "approval_workflow_bypassed",
    "approval_record_missing",
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

REQUEST_TYPES = {
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

STATES = {
    "drafted",
    "submitted",
    "intake_review",
    "evidence_required",
    "adr_required",
    "gate_required",
    "security_review_required",
    "architecture_review_required",
    "operator_review_required",
    "queued_for_future_decision",
    "rejected",
    "expired",
    "revoked",
    "implementation_unapproved",
}


def test_v02_workstream_proposal_registry_docs_exist_and_are_indexed() -> None:
    for relative in DOCS:
        assert (ROOT / relative).exists(), relative

    index = _text("docs/adr/README.md")
    assert "0117-v02-workstream-proposal-registry.md" in index

    registry = _text("docs/release/v02-workstream-proposal-registry.md")
    for heading in [
        "## Purpose",
        "## Scope",
        "## Registry Rules",
        "## Allowed Proposal States",
        "## Required Proposal Fields",
        "## Required Evidence",
        "## Required ADR Dependency",
        "## Required Gate Dependency",
        "## Approval Status Default False",
        "## Implementation Status Default False",
        "## No-Go Conditions",
        "## No v0.2 Tag Or Release",
    ]:
        assert heading in registry
    assert "AION-126 explicitly creates no v0.2 tag and no release" in registry

    request_index = _text("docs/release/v02-implementation-request-index.md")
    for request_type in REQUEST_TYPES:
        assert request_type in request_index
    for required in [
        "request ID",
        "workstream",
        "status",
        "implementation approved",
        "required ADR",
        "required gate",
        "required evidence",
        "blocker",
        "next planning action",
    ]:
        assert required in request_index

    queue = _text("docs/release/v02-approval-queue-preview.md")
    for required in [
        "## Queue Purpose",
        "## Queue State Is Preview-Only",
        "## Queue Does Not Approve Implementation",
        "## Queue Does Not Enable Runtime",
        "## Required Reviewers",
        "## Required Evidence",
        "## Expiry And Revocation Rules",
        "## Dual-Control Requirement",
        "## Approval Status Remains False",
        "## No-Go Conditions",
    ]:
        assert required in queue

    review_rules = _text("docs/release/v02-proposal-review-rules.md")
    for required in [
        "## Intake Validation",
        "## Duplicate Proposal Handling",
        "## Missing Evidence Rejection",
        "## Unsupported Runtime Capability Rejection",
        "## Security Review Requirement",
        "## Architecture Review Requirement",
        "## Operator Review Requirement",
        "## Rollback/Audit Requirement",
        "## ADR And Gate Dependency Requirement",
        "## No Direct Implementation Approval",
    ]:
        assert required in review_rules

    state_machine = _text("docs/release/v02-proposal-state-machine.md")
    for state in STATES:
        assert state in state_machine
    assert "No state enables runtime or approves implementation" in state_machine

    evidence = _text("docs/release/v02-proposal-evidence-requirements.md")
    for required in [
        "## Problem Statement",
        "## Risk Statement",
        "## Security Impact",
        "## Architecture Impact",
        "## Policy Impact",
        "## Audit/Provenance Impact",
        "## Rollback Plan",
        "## ADR Dependency",
        "## Gate Dependency",
        "## Test Evidence",
        "## No-Go Acknowledgement",
    ]:
        assert required in evidence

    no_go = _text("docs/release/v02-proposal-registry-no-go.md")
    for condition in [
        "implementation approval set true",
        "workstream implementation approval set true",
        "proposal state implies implementation approved",
        "approval queue item marked approved",
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

    adr = _text("docs/adr/0117-v02-workstream-proposal-registry.md")
    assert "Decision: add v0.2 workstream proposal registry." in adr
    assert "Decision: AION-126 does not approve implementation." in adr
    assert "Decision: proposal registry and approval queue remain preview-only." in adr
    assert (
        "Decision: future implementation still requires explicit approval records, "
        "ADRs, and gate evidence."
        in adr
    )
    assert "Decision: no v0.2 release or tag is created." in adr
    assert (
        "Reason: AION needs a controlled proposal registry before any "
        "implementation workstream can be approved."
        in adr
    )
    assert (
        "Consequence: future workstreams must enter through the registry and "
        "remain blocked until approval."
        in adr
    )
    assert "Constraint: no runtime enablement." in adr
    assert "Constraint: no external calls." in adr
    assert "Constraint: no credentials/tokens." in adr
    assert "Constraint: no sandbox execution." in adr
    assert "Constraint: no privileged bypass." in adr


def test_v02_workstream_proposal_registry_examples_are_safe() -> None:
    for relative in EXAMPLES:
        payload = _json(relative)
        if relative.startswith("examples/"):
            assert payload["synthetic"] is True
        assert payload["status"] == "passed"
        assert payload["task_id"] == "AION-126"
        assert payload["v02_workstream_proposal_registry_created"] is True
        assert payload["proposal_registry_preview_only"] is True
        assert payload["approval_queue_preview_only"] is True
        _assert_false_keys(payload, relative)

    request_payload = _json("examples/release/v02-implementation-request-index.json")
    assert {item["request_type"] for item in request_payload["requests"]} == REQUEST_TYPES
    for item in request_payload["requests"]:
        assert item["implementation_approved"] is False
        assert item["required_adr"]
        assert item["required_gate"]
        assert item["required_evidence"]
        assert item["blocker"]
        assert item["next_planning_action"]

    state_payload = _json("examples/release/v02-proposal-state-machine.json")
    assert set(state_payload["states"]) == STATES
    assert state_payload["runtime_enabling_states"] == []
    assert state_payload["implementation_approval_states"] == []


def test_v02_workstream_proposal_registry_scripts_are_executable_and_pass() -> None:
    scripts = [
        ROOT / "scripts/v02-workstream-proposal-registry-check.sh",
        ROOT / "scripts/v02-proposal-registry-freeze.sh",
        ROOT / "scripts/v02-proposal-registry-no-go-regression.sh",
    ]
    for script in scripts:
        assert script.exists()
        assert os.access(script, os.X_OK)
        assert script.stat().st_mode & stat.S_IXUSR
        subprocess.run(["bash", "-n", str(script)], cwd=ROOT, check=True)

    env = os.environ.copy()
    env["AION_V02_PROPOSAL_REGISTRY_FREEZE_SKIP_FULL_CHECK"] = "1"
    env["AION_V02_PREIMPLEMENTATION_MASTER_SKIP_NESTED_GATES"] = "1"
    env["AION_V02_PREIMPLEMENTATION_BASELINE_SKIP_FULL_CHECK"] = "1"
    subprocess.run(
        ["./scripts/v02-proposal-registry-no-go-regression.sh"],
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
            if key in {"implementation_approved", "approval_queue_item_approved"}:
                assert nested is False, f"{context}.{key} must be false"
            _assert_false_keys(nested, f"{context}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _assert_false_keys(item, f"{context}[{index}]")
