"""AION-138 v0.2 decision package preview regression tests."""

from __future__ import annotations

import json
import os
import stat
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]

DOCS = [
    "docs/release/v02-decision-package-preview.md",
    "docs/release/v02-approval-readiness-evidence-bundle.md",
    "docs/release/v02-runtime-decision-boundary.md",
    "docs/release/v02-decision-package-state-model.md",
    "docs/release/v02-decision-package-evidence-matrix.md",
    "docs/release/v02-decision-package-no-go.md",
    "docs/release/v02-decision-package-checklist.md",
    "docs/adr/0129-v02-decision-package-preview.md",
]

EXAMPLES = [
    "examples/release/v02-decision-package-preview.json",
    "examples/release/v02-approval-readiness-evidence-bundle.json",
    "examples/release/v02-runtime-decision-boundary.json",
    "examples/release/v02-decision-package-state-model.json",
    "examples/release/v02-decision-package-evidence-matrix.json",
    "operator-console-static/demo-data/v02-decision-package-preview.json",
    "operator-console-static/demo-data/v02-approval-readiness-evidence-bundle.json",
]

TRUE_KEYS = {
    "v02_decision_package_preview_created",
    "decision_package_preview_only",
    "review_board_planning_only",
    "submission_registry_preview_only",
    "preapproval_queue_preview_only",
    "proposal_registry_preview_only",
    "approval_queue_preview_only",
}

FALSE_KEYS = {
    "decision_package_approval",
    "approval_readiness_approved",
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


def test_v02_decision_package_docs_exist_and_are_indexed() -> None:
    for relative in DOCS:
        assert (ROOT / relative).exists(), relative

    assert "0129-v02-decision-package-preview.md" in _text("docs/adr/README.md")

    preview = _text("docs/release/v02-decision-package-preview.md")
    for required in [
        "## Purpose",
        "## Scope",
        "## Required Prior Gates",
        "## Package Contents",
        "## Approval Lock",
        "## Runtime Boundary",
        "## Static Console Evidence",
        "## No-Go Conditions",
        "AION-138 creates no v0.2 tag and no v0.2 release.",
    ]:
        assert required in preview

    bundle = _text("docs/release/v02-approval-readiness-evidence-bundle.md")
    for required in [
        "Review board stabilization",
        "Submission registry",
        "Request pack",
        "Proposal registry",
        "Planning closeout",
        "Runtime boundary",
        "decision_package_approval=false",
        "approval_readiness_approved=false",
    ]:
        assert required in bundle

    boundary = _text("docs/release/v02-runtime-decision-boundary.md")
    for candidate in [
        "Production auth implementation",
        "Connector runtime implementation",
        "Credential store implementation",
        "Sandbox runtime implementation",
        "Operator write execution",
        "Module activation",
        "AION-138 cannot create a release or tag.",
    ]:
        assert candidate in boundary

    model = _text("docs/release/v02-decision-package-state-model.md")
    for state in [
        "evidence_collected",
        "routed_for_review",
        "package_preview_created",
        "readiness_evidence_bundled",
        "blocked_for_approval",
        "future_decision_required",
        "keeps every approval false",
    ]:
        assert state in model

    matrix = _text("docs/release/v02-decision-package-evidence-matrix.md")
    for required in [
        "v02-decision-package-preview.md",
        "v02-approval-readiness-evidence-bundle.md",
        "v02-runtime-decision-boundary.md",
        "v02-decision-package-state-model.md",
        "v02-decision-package-no-go.md",
        "./scripts/v02-decision-package-preview-check.sh",
        "./scripts/v02-decision-package-freeze.sh",
        "./scripts/v02-decision-package-no-go-regression.sh",
    ]:
        assert required in matrix

    no_go = _text("docs/release/v02-decision-package-no-go.md")
    for condition in [
        "decision package approval true",
        "approval readiness approved true",
        "review board decision approval true",
        "routing decision approval true",
        "preapproval queue item approved true",
        "submission approval true",
        "request pack approval true",
        "runtime implementation approval true",
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
        "credential storage enabled",
        "token storage enabled",
        "sandbox execution enabled",
        "package files added",
        "migrations added",
        "runtime API execution routes added",
        "SDK resource implementation added",
        "CLI command implementation added",
        "frontend dependencies added",
        "privileged bypass",
    ]:
        assert condition in no_go

    checklist = _text("docs/release/v02-decision-package-checklist.md")
    for item in [
        "decision package preview docs complete",
        "approval readiness evidence bundle complete",
        "runtime decision boundary complete",
        "ADR 0129 indexed",
        "examples valid",
        "static console demo data read-only",
        "preview script executable and passing",
        "freeze script executable and passing",
        "no-go regression executable and passing",
        "no decision package approval",
        "no approval readiness approval",
        "no runtime implementation",
        "no v0.2 tag",
        "no v0.2 release",
    ]:
        assert item in checklist

    adr = _text("docs/adr/0129-v02-decision-package-preview.md")
    for required in [
        "Decision: add v0.2 decision package preview.",
        "Decision: AION-138 does not approve the decision package.",
        "Decision: approval readiness remains evidence only.",
        "Decision: decision package approval remains false.",
        "Decision: approval readiness approved remains false.",
        "Decision: future runtime implementation still requires explicit "
        "approval records, ADRs, and gate evidence.",
        "Decision: no v0.2 release or tag is created.",
        "Constraint: no runtime enablement.",
        "Constraint: no external calls.",
        "Constraint: no credentials/tokens.",
        "Constraint: no sandbox execution.",
        "Constraint: no privileged bypass.",
    ]:
        assert required in adr


def test_v02_decision_package_examples_are_safe() -> None:
    for relative in EXAMPLES:
        payload = _json(relative)
        assert payload["task_id"] == "AION-138"
        assert payload["status"] == "passed"
        assert payload["synthetic"] is True
        for key in TRUE_KEYS:
            assert payload[key] is True, f"{relative}.{key} must be true"
        _assert_false_keys(payload, relative)

    boundary = _json("examples/release/v02-runtime-decision-boundary.json")
    assert boundary["candidates"]
    for candidate in boundary["candidates"]:
        assert candidate["decision_state"] == "not approved"
        assert candidate["runtime_enabled"] is False

    model = _json("examples/release/v02-decision-package-state-model.json")
    assert len(model["states"]) == 6
    assert all(state["approval"] is False for state in model["states"])

    matrix = _json("examples/release/v02-decision-package-evidence-matrix.json")
    assert matrix["matrix"]
    assert all(row["present"] is True for row in matrix["matrix"])
    assert all(row["approval"] is False for row in matrix["matrix"])

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


def test_v02_decision_package_scripts_are_executable_and_pass() -> None:
    scripts = [
        ROOT / "scripts/v02-decision-package-preview-check.sh",
        ROOT / "scripts/v02-decision-package-freeze.sh",
        ROOT / "scripts/v02-decision-package-no-go-regression.sh",
    ]
    for script in scripts:
        assert script.exists(), script
        assert script.stat().st_mode & stat.S_IXUSR, script
        subprocess.run(["bash", "-n", str(script)], cwd=ROOT, check=True)

    env = {
        **os.environ,
        "AION_V02_DECISION_PACKAGE_PREVIEW_SKIP_INHERITED_GATES": "1",
        "AION_V02_DECISION_PACKAGE_FREEZE_SKIP_FULL_CHECK": "1",
    }
    for command in [
        "./scripts/v02-decision-package-preview-check.sh",
        "./scripts/v02-decision-package-freeze.sh",
        "./scripts/v02-decision-package-no-go-regression.sh",
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
