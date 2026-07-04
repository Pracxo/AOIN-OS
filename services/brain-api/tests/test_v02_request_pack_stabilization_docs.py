"""AION-132 v0.2 request pack stabilization regression tests."""

from __future__ import annotations

import json
import os
import stat
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]

DOCS = [
    "docs/release/v02-request-pack-stabilization-gate.md",
    "docs/release/v02-evidence-completeness-gate.md",
    "docs/release/v02-submission-freeze.md",
    "docs/release/v02-request-pack-closeout-checklist.md",
    "docs/release/v02-evidence-deficiency-register.md",
    "docs/release/v02-submission-review-matrix.md",
    "docs/release/v02-request-pack-stabilization-no-go.md",
    "docs/adr/0123-v02-request-pack-stabilization.md",
]

EXAMPLES = [
    "examples/release/v02-request-pack-stabilization-gate.json",
    "examples/release/v02-evidence-completeness-gate.json",
    "examples/release/v02-submission-freeze.json",
    "examples/release/v02-evidence-deficiency-register.json",
    "examples/release/v02-submission-review-matrix.json",
    "operator-console-static/demo-data/v02-request-pack-stabilization.json",
    "operator-console-static/demo-data/v02-evidence-completeness-gate.json",
]

FALSE_KEYS = {
    "request_pack_approval",
    "request_package_implementation_approved",
    "proposal_template_implementation_approved",
    "approval_evidence_approval_true",
    "evidence_completeness_bypassed",
    "submission_freeze_bypassed",
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
    "secrets_present",
    "tokens_present",
    "credentials_present",
    "endpoints_present",
    "prompt_payloads_present",
    "private_reasoning_present",
}

EVIDENCE_ITEMS = [
    "problem statement",
    "risk statement",
    "security impact",
    "architecture impact",
    "policy impact",
    "audit/provenance impact",
    "rollback plan",
    "ADR dependency",
    "gate dependency",
    "test evidence",
    "no-go acknowledgement",
    "approval status false",
]


def test_v02_request_pack_stabilization_docs_exist_and_are_indexed() -> None:
    for relative in DOCS:
        assert (ROOT / relative).exists(), relative

    index = _text("docs/adr/README.md")
    assert "0123-v02-request-pack-stabilization.md" in index

    gate = _text("docs/release/v02-request-pack-stabilization-gate.md")
    for heading in [
        "## Purpose",
        "## Scope",
        "## Required Prior Gates",
        "## Request Pack Evidence",
        "## Proposal Template Evidence",
        "## Approval Evidence Boundary",
        "## Evidence Completeness Gate",
        "## Submission Freeze State",
        "## Implementation Approval Lock Checks",
        "## No-Go Conditions",
        "## No v0.2 Tag Or Release",
    ]:
        assert heading in gate
    for required in [
        "request_pack_approval=false",
        "approval_queue_item_approved=false",
        "proposal_implementation_approved=false",
        "runtime_implementation_approved=false",
        "no v0.2 tag",
        "no v0.2 release",
    ]:
        assert required in gate

    completeness = _text("docs/release/v02-evidence-completeness-gate.md").lower()
    for item in EVIDENCE_ITEMS:
        assert item.lower() in completeness

    freeze = " ".join(_text("docs/release/v02-submission-freeze.md").lower().split())
    for required in [
        "request submissions are template-only",
        "request pack remains preview-only",
        "proposal registry remains preview-only",
        "approval queue remains preview-only",
        "approval queue item approval remains false",
        "request pack approval remains false",
        "proposal implementation approval remains false",
        "runtime implementation approval remains false",
        "no runtime capability is enabled",
        "no v0.2 tag or release is created",
    ]:
        assert required in freeze

    checklist = _text("docs/release/v02-request-pack-closeout-checklist.md")
    for item in [
        "docs complete",
        "examples valid",
        "scripts executable",
        "request pack check passing",
        "request pack freeze passing",
        "request pack no-go regression passing",
        "planning track closeout passing",
        "final planning release gate passing",
        "proposal registry stabilization passing",
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

    deficiency = _text("docs/release/v02-evidence-deficiency-register.md")
    for item in [f"missing {name}" for name in EVIDENCE_ITEMS[:-1]]:
        assert item in deficiency
    assert "approval status not false" in deficiency
    for column in ["Deficiency", "Consequence", "Required correction"]:
        assert column in deficiency
    for column in ["Release blocker", "Approval blocker"]:
        assert column in deficiency

    matrix = _text("docs/release/v02-submission-review-matrix.md")
    for column in [
        "Submission field",
        "Required evidence",
        "Reviewer",
        "Gate dependency",
        "Approval state",
        "Release blocker if violated",
        "Notes",
    ]:
        assert column in matrix

    no_go = _text("docs/release/v02-request-pack-stabilization-no-go.md")
    for condition in [
        "request pack marks implementation approved",
        "request pack approval true",
        "proposal template marks implementation approved",
        "approval evidence marks approval true",
        "evidence completeness bypassed",
        "submission freeze bypassed",
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

    adr = _text("docs/adr/0123-v02-request-pack-stabilization.md")
    for required in [
        "Decision: add v0.2 request pack stabilization gate.",
        "Decision: AION-132 does not approve implementation.",
        "Decision: request packs and submission templates remain planning-only.",
        "Decision: evidence completeness does not approve implementation by itself.",
        "Decision: no v0.2 release or tag is created.",
        (
            "Reason: AION needs complete request evidence before "
            "implementation proposals can be reviewed."
        ),
        (
            "Consequence: future workstream requests must pass evidence "
            "completeness and submission freeze checks."
        ),
        "Constraint: no runtime enablement.",
        "Constraint: no external calls.",
        "Constraint: no credentials/tokens.",
        "Constraint: no sandbox execution.",
        "Constraint: no privileged bypass.",
    ]:
        assert required in adr


def test_v02_request_pack_stabilization_examples_are_safe() -> None:
    for relative in EXAMPLES:
        payload = _json(relative)
        assert payload["task_id"] == "AION-132"
        assert payload["status"] == "passed"
        assert payload["synthetic"] is True
        assert payload["v02_request_pack_stabilized"] is True
        assert payload["evidence_completeness_gate_created"] is True
        assert payload["submission_freeze_created"] is True
        assert payload["request_pack_preview_only"] is True
        assert payload["proposal_registry_preview_only"] is True
        assert payload["approval_queue_preview_only"] is True
        _assert_false_keys(payload, relative)

    completeness = _json("examples/release/v02-evidence-completeness-gate.json")
    assert completeness["required_evidence"] == EVIDENCE_ITEMS

    deficiency = _json("examples/release/v02-evidence-deficiency-register.json")
    assert len(deficiency["deficiencies"]) == len(EVIDENCE_ITEMS)
    assert all(item["release_blocker"] is True for item in deficiency["deficiencies"])
    assert all(item["approval_blocker"] is True for item in deficiency["deficiencies"])

    matrix = _json("examples/release/v02-submission-review-matrix.json")
    assert len(matrix["matrix"]) == len(EVIDENCE_ITEMS)
    for row in matrix["matrix"]:
        assert row["approval_state"] is False
        assert row["release_blocker_if_violated"] is True

    for relative in EXAMPLES[-2:]:
        payload = _json(relative)
        assert payload["read_only"] is True
        assert payload["redaction_applied"] is True
        assert payload["sections"]
        assert payload["blockers"]
        assert payload["warnings"]
        assert payload["refs"]
        assert payload["forbidden_actions"]


def test_v02_request_pack_stabilization_scripts_are_executable_and_pass() -> None:
    scripts = [
        ROOT / "scripts/v02-request-pack-stabilization-gate.sh",
        ROOT / "scripts/v02-request-pack-submission-freeze.sh",
        ROOT / "scripts/v02-request-pack-stabilization-no-go-regression.sh",
    ]
    for script in scripts:
        assert script.exists(), script
        assert script.stat().st_mode & stat.S_IXUSR, script
        subprocess.run(["bash", "-n", str(script)], cwd=ROOT, check=True)

    env = {
        **os.environ,
        "AION_V02_REQUEST_PACK_STABILIZATION_SKIP_INHERITED_GATES": "1",
        "AION_V02_REQUEST_PACK_SUBMISSION_FREEZE_SKIP_FULL_CHECK": "1",
    }
    for command in [
        "./scripts/v02-request-pack-stabilization-gate.sh",
        "./scripts/v02-request-pack-submission-freeze.sh",
        "./scripts/v02-request-pack-stabilization-no-go-regression.sh",
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
            if key in {"implementation_approved", "approval_state"}:
                assert nested is False, f"{context}.{key} must be false"
            _assert_false_keys(nested, f"{context}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _assert_false_keys(item, f"{context}[{index}]")
