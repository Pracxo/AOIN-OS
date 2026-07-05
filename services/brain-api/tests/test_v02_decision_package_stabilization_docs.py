"""AION-139 v0.2 decision package stabilization regression tests."""

from __future__ import annotations

import json
import os
import stat
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]

DOCS = [
    "docs/release/v02-decision-package-stabilization-gate.md",
    "docs/release/v02-approval-readiness-freeze.md",
    "docs/release/v02-runtime-decision-closeout-boundary.md",
    "docs/release/v02-decision-package-evidence-baseline.md",
    "docs/release/v02-decision-readiness-status-summary.md",
    "docs/release/v02-decision-package-stabilization-no-go.md",
    "docs/release/v02-decision-package-closeout-checklist.md",
    "docs/adr/0130-v02-decision-package-stabilization.md",
]

EXAMPLES = [
    "examples/release/v02-decision-package-stabilization-gate.json",
    "examples/release/v02-approval-readiness-freeze.json",
    "examples/release/v02-runtime-decision-closeout-boundary.json",
    "examples/release/v02-decision-package-evidence-baseline.json",
    "examples/release/v02-decision-readiness-status-summary.json",
    "operator-console-static/demo-data/v02-decision-package-stabilization.json",
    "operator-console-static/demo-data/v02-approval-readiness-freeze.json",
]

TRUE_KEYS = {
    "v02_decision_package_stabilized",
    "decision_package_preview_only",
    "approval_readiness_preview_only",
    "review_board_planning_only",
    "submission_registry_preview_only",
    "preapproval_queue_preview_only",
    "proposal_registry_preview_only",
    "approval_queue_preview_only",
}

FALSE_KEYS = {
    "decision_package_approval",
    "approval_readiness_approved",
    "runtime_decision_readiness_approved",
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

FORBIDDEN_ACTIONS = {
    "activate_module",
    "activate_capability",
    "load_code",
    "execute_tool",
    "enable_external_model_calls",
    "hard_delete",
}


def test_v02_decision_package_stabilization_docs_exist_and_are_indexed() -> None:
    for relative in DOCS:
        assert (ROOT / relative).exists(), relative

    assert "0130-v02-decision-package-stabilization.md" in _text("docs/adr/README.md")

    gate = _text("docs/release/v02-decision-package-stabilization-gate.md")
    for required in [
        "## Purpose",
        "## Scope",
        "## Required Prior Gates",
        "## Decision Package Preview Evidence",
        "## Approval Readiness Evidence",
        "## Runtime Decision Boundary Evidence",
        "## Decision Package State Evidence",
        "## Approval Lock Checks",
        "## No-Go Conditions",
        "AION-139 creates no v0.2 tag and no v0.2 release.",
    ]:
        assert required in gate

    freeze = _text("docs/release/v02-approval-readiness-freeze.md")
    for required in [
        "Approval readiness remains preview-only",
        "Approval readiness does not approve",
        "implementation, does not enable runtime",
        "decision_package_approval=false",
        "approval_readiness_approved=false",
        "runtime_decision_readiness_approved=false",
        "review_board_decision_approval=false",
        "routing_decision_approval=false",
        "reviewer_signoff_implementation_approval=false",
        "ADR 0130",
    ]:
        assert required in freeze

    boundary = _text("docs/release/v02-runtime-decision-closeout-boundary.md")
    for required in [
        "Runtime decision readiness is not implementation approval",
        "Decision package completeness is not implementation approval",
        "Approval readiness completeness is not runtime enablement",
        "Reviewer evidence is not implementation approval",
        "Review board routing is not implementation approval",
        "ADR dependency presence is not runtime enablement",
        "Gate dependency success is not runtime enablement",
        "runtime_implementation_approved=false",
        "runtime_decision_readiness_approved=false",
        "decision_package_approval=false",
        "approval_readiness_approved=false",
        "v02_release_approved=false",
    ]:
        assert required in boundary

    baseline = _text("docs/release/v02-decision-package-evidence-baseline.md")
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
        assert candidate in baseline

    summary = _text("docs/release/v02-decision-readiness-status-summary.md")
    for required in [
        "decision_package_stabilized=true",
        "decision_package_preview_only=true",
        "decision_package_approval=false",
        "approval_readiness_preview_only=true",
        "approval_readiness_approved=false",
        "runtime_decision_readiness_approved=false",
        "review_board_decision_approval=false",
        "routing_decision_approval=false",
        "reviewer_signoff_implementation_approval=false",
        "submission_registry_preview_only=true",
        "preapproval_queue_preview_only=true",
        "request_pack_approval=false",
        "submission_approval=false",
        "runtime_implementation_approved=false",
        "v02_tag_created=false",
        "v02_release_created=false",
    ]:
        assert required in summary

    no_go = _text("docs/release/v02-decision-package-stabilization-no-go.md")
    for condition in [
        "decision package approval true",
        "approval readiness approved true",
        "runtime decision readiness approved true",
        "review board decision approval true",
        "routing decision approval true",
        "preapproval queue item approved true",
        "submission approval true",
        "request pack approval true",
        "implementation approval true",
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

    checklist = _text("docs/release/v02-decision-package-closeout-checklist.md")
    for item in [
        "docs complete",
        "examples valid",
        "scripts executable",
        "decision package preview passing",
        "decision package freeze passing",
        "decision package no-go regression passing",
        "review board stabilization passing",
        "no decision package approval",
        "no approval readiness approval",
        "no runtime decision readiness approval",
        "no runtime implementation",
        "no v0.2 tag",
        "no v0.2 release",
    ]:
        assert item in checklist

    adr = _text("docs/adr/0130-v02-decision-package-stabilization.md")
    for required in [
        "Decision: add v0.2 decision package stabilization gate.",
        "Decision: AION-139 does not approve implementation.",
        "Decision: decision packages and approval readiness bundles remain preview-only.",
        "Decision: decision package approval remains false.",
        "Decision: approval readiness approval remains false.",
        "Decision: runtime decision readiness approval remains false.",
        (
            "Decision: future implementation still requires explicit approval records, "
            "ADRs, and gate evidence."
        ),
        "Decision: no v0.2 release or tag is created.",
        "Constraint: no runtime enablement.",
        "Constraint: no external calls.",
        "Constraint: no credentials/tokens.",
        "Constraint: no sandbox execution.",
        "Constraint: no privileged bypass.",
    ]:
        assert required in adr


def test_v02_decision_package_stabilization_examples_are_safe() -> None:
    for relative in EXAMPLES:
        payload = _json(relative)
        assert payload["task_id"] == "AION-139"
        assert payload["status"] == "passed"
        assert payload["synthetic"] is True
        for key in TRUE_KEYS:
            assert payload[key] is True, f"{relative}.{key} must be true"
        _assert_false_keys(payload, relative)

    boundary = _json("examples/release/v02-runtime-decision-closeout-boundary.json")
    assert boundary["candidates"]
    for candidate in boundary["candidates"]:
        assert candidate["runtime_enabled"] is False
        assert candidate["runtime_decision_readiness_approved"] is False

    baseline = _json("examples/release/v02-decision-package-evidence-baseline.json")
    assert len(baseline["candidate_areas"]) == 10

    for relative in EXAMPLES[-2:]:
        payload = _json(relative)
        assert payload["read_only"] is True
        assert payload["redaction_applied"] is True
        assert payload["sections"]
        assert payload["blockers"]
        assert payload["warnings"]
        assert payload["refs"]
        assert payload["forbidden_actions"]
        action_keys = {action["action_key"] for action in payload["forbidden_actions"]}
        assert action_keys == FORBIDDEN_ACTIONS
        for action in payload["forbidden_actions"]:
            assert action["allowed"] is False


def test_v02_decision_package_stabilization_scripts_are_executable_and_pass() -> None:
    scripts = [
        ROOT / "scripts/v02-decision-package-stabilization-gate.sh",
        ROOT / "scripts/v02-approval-readiness-freeze.sh",
        ROOT / "scripts/v02-decision-package-stabilization-no-go-regression.sh",
    ]
    for script in scripts:
        assert script.exists(), script
        assert script.stat().st_mode & stat.S_IXUSR, script
        subprocess.run(["bash", "-n", str(script)], cwd=ROOT, check=True)

    env = {
        **os.environ,
        "AION_V02_DECISION_PACKAGE_STABILIZATION_SKIP_INHERITED_GATES": "1",
        "AION_V02_APPROVAL_READINESS_FREEZE_SKIP_FULL_CHECK": "1",
    }
    for command in [
        "./scripts/v02-decision-package-stabilization-gate.sh",
        "./scripts/v02-approval-readiness-freeze.sh",
        "./scripts/v02-decision-package-stabilization-no-go-regression.sh",
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
