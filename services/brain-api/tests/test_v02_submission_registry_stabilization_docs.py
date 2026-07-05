"""AION-135 v0.2 submission registry stabilization regression tests."""

from __future__ import annotations

import json
import os
import stat
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]

DOCS = [
    "docs/release/v02-submission-registry-stabilization-gate.md",
    "docs/release/v02-preapproval-queue-freeze.md",
    "docs/release/v02-request-candidate-closeout-baseline.md",
    "docs/release/v02-submission-lifecycle-evidence-baseline.md",
    "docs/release/v02-submission-registry-closeout-checklist.md",
    "docs/release/v02-preapproval-queue-stabilization-no-go.md",
    "docs/release/v02-submission-registry-stabilization-summary.md",
    "docs/adr/0126-v02-submission-registry-stabilization.md",
]

EXAMPLES = [
    "examples/release/v02-submission-registry-stabilization-gate.json",
    "examples/release/v02-preapproval-queue-freeze.json",
    "examples/release/v02-request-candidate-closeout-baseline.json",
    "examples/release/v02-submission-lifecycle-evidence-baseline.json",
    "examples/release/v02-submission-registry-closeout-result.json",
    "operator-console-static/demo-data/v02-submission-registry-stabilization.json",
    "operator-console-static/demo-data/v02-preapproval-queue-freeze.json",
]

FALSE_KEYS = {
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
    "api_runtime_execution_route_added",
    "secrets_present",
    "tokens_present",
    "credentials_present",
    "endpoints_present",
    "prompt_payloads_present",
    "private_reasoning_present",
}

TRUE_KEYS = {
    "v02_submission_registry_stabilized",
    "submission_registry_stabilized",
    "submission_registry_preview_only",
    "preapproval_queue_preview_only",
    "proposal_registry_preview_only",
    "approval_queue_preview_only",
}


def test_v02_submission_registry_stabilization_docs_exist_and_are_indexed() -> None:
    for relative in DOCS:
        assert (ROOT / relative).exists(), relative

    index = _text("docs/adr/README.md")
    assert "0126-v02-submission-registry-stabilization.md" in index

    gate = _text("docs/release/v02-submission-registry-stabilization-gate.md")
    for heading in [
        "## Purpose",
        "## Scope",
        "## Required Prior Gates",
        "## Submission Registry Evidence",
        "## Pre-Approval Queue Evidence",
        "## Request Candidate Evidence",
        "## Submission Lifecycle Evidence",
        "## Approval Lock Checks",
        "## No-Go Conditions",
        "## No Tag Or Release",
    ]:
        assert heading in gate
    for required in [
        "Submission approval remains false",
        "implementation approval false",
        "no v0.2 tag",
        "no v0.2 release",
    ]:
        assert required in gate

    queue = _text("docs/release/v02-preapproval-queue-freeze.md")
    for required in [
        "Pre-approval queue remains preview-only.",
        "Queue does not approve implementation.",
        "Queue does not enable runtime.",
        "Pre-approval queue item approval remains false.",
        "Submission approval remains false.",
        "Request pack approval remains false.",
        "Required Reviewers",
        "Required Evidence",
        "ADR Dependency Requirement",
        "Gate Dependency Requirement",
        "Expiry And Revocation Expectations",
        "No-Go Conditions",
    ]:
        assert required in queue

    candidates = _text("docs/release/v02-request-candidate-closeout-baseline.md")
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
        assert candidate in candidates
    for column in [
        "Candidate ID",
        "Workstream",
        "Submission status",
        "Pre-approval queue status",
        "Submission approval",
        "Implementation approval",
        "Required ADR",
        "Required gate",
        "Required evidence",
        "Blocker",
        "Next planning action",
    ]:
        assert column in candidates

    lifecycle = _text("docs/release/v02-submission-lifecycle-evidence-baseline.md")
    for column in [
        "Submission state",
        "Required evidence",
        "Required reviewer",
        "Required ADR",
        "Required gate",
        "Allowed today",
        "Submission approved",
        "Implementation approved",
        "Runtime enabled",
        "Release blocker if violated",
        "Notes",
    ]:
        assert column in lifecycle
    assert "No lifecycle state approves implementation or enables runtime." in lifecycle

    checklist = _text("docs/release/v02-submission-registry-closeout-checklist.md")
    for item in [
        "docs complete",
        "examples valid",
        "scripts executable",
        "submission registry preview passing",
        "pre-approval queue freeze passing",
        "submission registry no-go regression passing",
        "request pack final review passing",
        "request pack stabilization passing",
        "implementation request pack check passing",
        "planning track closeout passing",
        "final planning release gate passing",
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

    no_go = _text("docs/release/v02-preapproval-queue-stabilization-no-go.md")
    for condition in [
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

    summary = _text("docs/release/v02-submission-registry-stabilization-summary.md")
    for required in [
        "submission_registry_stabilized=true",
        "preapproval_queue_item_approved=false",
        "submission_approval=false",
        "request_pack_approval=false",
        "runtime_implementation_approved=false",
        "workstream_implementation_approved=false",
        "proposal_implementation_approved=false",
        "v02_tag_created=false",
        "v02_release_created=false",
    ]:
        assert required in summary

    adr = _text("docs/adr/0126-v02-submission-registry-stabilization.md")
    for required in [
        "Decision: add v0.2 submission registry stabilization gate.",
        "Decision: AION-135 does not approve implementation.",
        "Decision: submission registry and pre-approval queue remain preview-only.",
        "Decision: submission approval and pre-approval queue item approval remain false.",
        "Decision: future implementation still requires explicit approval records",
        "Decision: no v0.2 release or tag is created.",
        "AION needs a stable pre-approval submission baseline before implementation",
        "Future implementation candidates remain blocked",
        "Constraint: no runtime enablement.",
        "Constraint: no external calls.",
        "Constraint: no credentials/tokens.",
        "Constraint: no sandbox execution.",
        "Constraint: no privileged bypass.",
    ]:
        assert required in adr


def test_v02_submission_registry_stabilization_examples_are_safe() -> None:
    for relative in EXAMPLES:
        payload = _json(relative)
        assert payload["task_id"] == "AION-135"
        assert payload["status"] == "passed"
        assert payload["synthetic"] is True
        for key in TRUE_KEYS:
            assert payload[key] is True, f"{relative}.{key} must be true"
        _assert_false_keys(payload, relative)

    candidate = _json("examples/release/v02-request-candidate-closeout-baseline.json")
    assert candidate["candidate_count"] == 10
    assert len(candidate["candidates"]) == 10
    for item in candidate["candidates"]:
        assert item["submission_approval"] is False
        assert item["implementation_approval"] is False

    lifecycle = _json("examples/release/v02-submission-lifecycle-evidence-baseline.json")
    assert len(lifecycle["states"]) == 15
    assert {state["submission_state"] for state in lifecycle["states"]} >= {
        "queued_for_preapproval_review",
        "submission_unapproved",
        "implementation_unapproved",
    }
    for state in lifecycle["states"]:
        assert state["submission_approved"] is False
        assert state["implementation_approved"] is False
        assert state["runtime_enabled"] is False

    closeout = _json("examples/release/v02-submission-registry-closeout-result.json")
    assert closeout["closeout"]["submission_registry_no_go_regression_passing"] is True

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


def test_v02_submission_registry_stabilization_scripts_are_executable_and_pass() -> None:
    scripts = [
        ROOT / "scripts/v02-submission-registry-stabilization-gate.sh",
        ROOT / "scripts/v02-submission-registry-freeze.sh",
        ROOT / "scripts/v02-submission-registry-stabilization-no-go-regression.sh",
    ]
    for script in scripts:
        assert script.exists(), script
        assert script.stat().st_mode & stat.S_IXUSR, script
        subprocess.run(["bash", "-n", str(script)], cwd=ROOT, check=True)

    env = {
        **os.environ,
        "AION_V02_SUBMISSION_REGISTRY_STABILIZATION_SKIP_INHERITED_GATES": "1",
        "AION_V02_SUBMISSION_REGISTRY_FREEZE_SKIP_FULL_CHECK": "1",
        "AION_V02_SUBMISSION_REGISTRY_PREVIEW_SKIP_INHERITED_GATES": "1",
        "AION_V02_PREAPPROVAL_QUEUE_FREEZE_SKIP_FULL_CHECK": "1",
    }
    for command in [
        "./scripts/v02-submission-registry-stabilization-gate.sh",
        "./scripts/v02-submission-registry-freeze.sh",
        "./scripts/v02-submission-registry-stabilization-no-go-regression.sh",
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
