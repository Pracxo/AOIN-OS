"""AION-133 v0.2 request pack final review regression tests."""

from __future__ import annotations

import json
import os
import stat
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]

DOCS = [
    "docs/release/v02-request-pack-final-review.md",
    "docs/release/v02-evidence-boundary-closeout.md",
    "docs/release/v02-preapproval-submission-gate.md",
    "docs/release/v02-request-approval-guard.md",
    "docs/release/v02-final-submission-evidence-matrix.md",
    "docs/release/v02-submission-no-go-review.md",
    "docs/release/v02-request-pack-final-checklist.md",
    "docs/adr/0124-v02-request-pack-final-review.md",
]

EXAMPLES = [
    "examples/release/v02-request-pack-final-review.json",
    "examples/release/v02-evidence-boundary-closeout.json",
    "examples/release/v02-preapproval-submission-gate.json",
    "examples/release/v02-request-approval-guard.json",
    "examples/release/v02-final-submission-evidence-matrix.json",
    "operator-console-static/demo-data/v02-request-pack-final-review.json",
    "operator-console-static/demo-data/v02-preapproval-submission-gate.json",
]

FALSE_KEYS = {
    "request_pack_approval",
    "submission_approval",
    "request_package_implementation_approved",
    "proposal_template_implementation_approved",
    "approval_evidence_approval_true",
    "evidence_completeness_bypassed",
    "submission_freeze_bypassed",
    "preapproval_gate_bypassed",
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

TRUE_KEYS = {
    "v02_request_pack_final_review_passed",
    "evidence_boundary_closed_out",
    "preapproval_submission_gate_created",
    "request_pack_preview_only",
    "proposal_registry_preview_only",
    "approval_queue_preview_only",
}


def test_v02_request_pack_final_review_docs_exist_and_are_indexed() -> None:
    for relative in DOCS:
        assert (ROOT / relative).exists(), relative

    index = _text("docs/adr/README.md")
    assert "0124-v02-request-pack-final-review.md" in index

    review = _text("docs/release/v02-request-pack-final-review.md")
    for heading in [
        "## Purpose",
        "## Scope",
        "## Required Prior Gates",
        "## AION-131 Summary",
        "## AION-132 Summary",
        "## Request Pack Final State",
        "## Evidence Completeness Final State",
        "## Submission Freeze Final State",
        "## Request Approval Guard",
        "## No-Go Conditions",
        "## No v0.2 Tag Or Release",
    ]:
        assert heading in review
    for required in [
        "request_pack_approval=false",
        "submission_approval=false",
        "runtime_implementation_approved=false",
        "workstream_implementation_approved=false",
        "proposal_implementation_approved=false",
        "no v0.2 tag",
        "no v0.2 release",
    ]:
        assert required in review

    closeout = _text("docs/release/v02-evidence-boundary-closeout.md")
    for required in [
        "The evidence boundary remains planning-only.",
        "Evidence does not approve implementation.",
        "Evidence does not enable runtime.",
        "ADR review does not enable runtime.",
        "Gate success does not enable runtime.",
        "Approval records remain explicit.",
        "The approval queue remains preview-only.",
        "Request pack approval remains false.",
    ]:
        assert required in closeout

    gate = _text("docs/release/v02-preapproval-submission-gate.md").lower()
    for required in [
        "submission purpose",
        "submission pre-approval only",
        "does not approve implementation",
        "does not approve runtime",
        "required request pack fields",
        "required evidence fields",
        "required adr dependency",
        "required gate dependency",
        "reviewer evidence",
        "no-go acknowledgement",
        "approval status default false",
    ]:
        assert required in gate

    guard = _text("docs/release/v02-request-approval-guard.md")
    for required in [
        "request_pack_approval=false",
        "submission_approval=false",
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
        assert required in guard

    matrix = _text("docs/release/v02-final-submission-evidence-matrix.md")
    for column in [
        "Submission area",
        "Required evidence",
        "Required reviewer",
        "Required ADR",
        "Required gate",
        "Approval state",
        "Implementation state",
        "Release blocker if violated",
        "Notes",
    ]:
        assert column in matrix

    no_go = _text("docs/release/v02-submission-no-go-review.md")
    for condition in [
        "request pack approval true",
        "submission approval true",
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

    checklist = _text("docs/release/v02-request-pack-final-checklist.md")
    for item in [
        "docs complete",
        "examples valid",
        "scripts executable",
        "request pack stabilization passing",
        "request pack final review passing",
        "preapproval submission gate passing",
        "submission no-go passing",
        "planning track closeout passing",
        "final planning release gate passing",
        "no runtime implementation",
        "no request approval",
        "no submission approval",
        "no v0.2 tag",
        "no v0.2 release",
        "no external calls",
        "no credentials/tokens",
        "no sandbox execution",
        "no package files",
        "no migrations",
    ]:
        assert item in checklist

    adr = _text("docs/adr/0124-v02-request-pack-final-review.md")
    for required in [
        "Decision: add v0.2 request pack final review.",
        "Decision: AION-133 does not approve implementation.",
        "Decision: request packs and submissions remain planning-only.",
        (
            "Decision: evidence completeness and pre-approval submission gates "
            "do not\napprove implementation."
        ),
        "Decision: no v0.2 release or tag is created.",
        (
            "Reason: AION needs a final request-pack review before any "
            "implementation\nrequest can enter approval consideration."
        ),
        (
            "Consequence: future workstream submissions must pass request pack final review\n"
            "and no-go checks."
        ),
        "Constraint: no runtime enablement.",
        "Constraint: no external calls.",
        "Constraint: no credentials/tokens.",
        "Constraint: no sandbox execution.",
        "Constraint: no privileged bypass.",
    ]:
        assert required in adr


def test_v02_request_pack_final_review_examples_are_safe() -> None:
    for relative in EXAMPLES:
        payload = _json(relative)
        assert payload["task_id"] == "AION-133"
        assert payload["status"] == "passed"
        assert payload["synthetic"] is True
        for key in TRUE_KEYS:
            assert payload[key] is True, f"{relative}.{key} must be true"
        _assert_false_keys(payload, relative)

    matrix = _json("examples/release/v02-final-submission-evidence-matrix.json")
    assert len(matrix["matrix"]) == 5
    for row in matrix["matrix"]:
        assert row["approval_state"] is False
        assert row["implementation_state"] is False
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


def test_v02_request_pack_final_review_scripts_are_executable_and_pass() -> None:
    scripts = [
        ROOT / "scripts/v02-request-pack-final-review.sh",
        ROOT / "scripts/v02-preapproval-submission-freeze.sh",
        ROOT / "scripts/v02-request-pack-final-no-go-regression.sh",
    ]
    for script in scripts:
        assert script.exists(), script
        assert script.stat().st_mode & stat.S_IXUSR, script
        subprocess.run(["bash", "-n", str(script)], cwd=ROOT, check=True)

    env = {
        **os.environ,
        "AION_V02_REQUEST_PACK_FINAL_REVIEW_SKIP_INHERITED_GATES": "1",
        "AION_V02_PREAPPROVAL_SUBMISSION_FREEZE_SKIP_FULL_CHECK": "1",
    }
    for command in [
        "./scripts/v02-request-pack-final-review.sh",
        "./scripts/v02-preapproval-submission-freeze.sh",
        "./scripts/v02-request-pack-final-no-go-regression.sh",
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
            if key in {"implementation_approved", "approval_state", "implementation_state"}:
                assert nested is False, f"{context}.{key} must be false"
            _assert_false_keys(nested, f"{context}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _assert_false_keys(item, f"{context}[{index}]")
