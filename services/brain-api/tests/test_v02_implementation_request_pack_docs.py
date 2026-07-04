"""AION-131 v0.2 implementation request pack regression tests."""

from __future__ import annotations

import json
import os
import stat
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]

DOCS = [
    "docs/release/v02-implementation-request-pack.md",
    "docs/release/v02-proposal-submission-templates.md",
    "docs/release/v02-approval-evidence-boundary.md",
    "docs/release/v02-implementation-request-evidence-checklist.md",
    "docs/release/v02-workstream-request-template-catalog.md",
    "docs/release/v02-request-package-review-rules.md",
    "docs/release/v02-request-package-no-go.md",
    "docs/adr/0122-v02-implementation-request-pack.md",
]

EXAMPLES = [
    "examples/release/v02-implementation-request-pack.json",
    "examples/release/v02-proposal-submission-template.json",
    "examples/release/v02-approval-evidence-boundary.json",
    "examples/release/v02-implementation-request-evidence-checklist.json",
    "examples/release/v02-workstream-request-template-catalog.json",
    "operator-console-static/demo-data/v02-implementation-request-pack.json",
    "operator-console-static/demo-data/v02-proposal-submission-templates.json",
]

FALSE_KEYS = {
    "request_package_implementation_approved",
    "proposal_template_implementation_approved",
    "approval_evidence_approval_true",
    "evidence_approves_implementation",
    "adr_review_enables_runtime",
    "gate_success_enables_runtime",
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


def test_v02_request_pack_docs_exist_and_are_indexed() -> None:
    for relative in DOCS:
        assert (ROOT / relative).exists(), relative

    index = _text("docs/adr/README.md")
    assert "0122-v02-implementation-request-pack.md" in index

    request_pack = _text("docs/release/v02-implementation-request-pack.md")
    for heading in [
        "## Purpose",
        "## Scope",
        "## Request Pack Contents",
        "## Required Proposal Fields",
        "## Required Evidence Fields",
        "## Required ADR Dependency",
        "## Required Gate Dependency",
        "## Required Security Review",
        "## Required Architecture Review",
        "## Required Operator Review",
        "## Required Rollback/Audit Plan",
        "## Default Implementation Approval False",
        "## No v0.2 Tag Or Release",
    ]:
        assert heading in request_pack
    for required in [
        "runtime_implementation_approved=false",
        "workstream_implementation_approved=false",
        "proposal_implementation_approved=false",
        "approval_queue_item_approved=false",
        "no v0.2 tag",
        "no v0.2 release",
    ]:
        assert required in request_pack

    templates = _text("docs/release/v02-proposal-submission-templates.md")
    for template in [
        "Production Auth Implementation Request",
        "Audit/Provenance Hardening Request",
        "Rollback/Recovery Request",
        "External Call Release Gate Request",
        "Connector Runtime Implementation Request",
        "Credential Store Implementation Request",
        "Sandbox Runtime Implementation Request",
        "Operator Write Execution Request",
        "Module Activation Request",
        "Production UI Decision Request",
    ]:
        assert template in templates
    for field in [
        "workstream",
        "problem statement",
        "proposed change",
        "runtime capability requested",
        "current approval state",
        "required ADR",
        "required gate",
        "required evidence",
        "security impact",
        "policy impact",
        "rollback/audit plan",
        "default approval status false",
    ]:
        assert field in templates

    boundary = _text("docs/release/v02-approval-evidence-boundary.md")
    for required in [
        "Evidence is required before approval",
        "Evidence does not approve implementation by itself",
        "ADR review does not enable runtime by itself",
        "Gate success does not enable runtime by itself",
        "Approval records must remain explicit",
        "The approval queue remains preview-only",
        "approval_queue_item_approved=false",
    ]:
        assert required in boundary

    checklist = _text("docs/release/v02-implementation-request-evidence-checklist.md")
    for item in [
        "problem statement present",
        "risk statement present",
        "security impact present",
        "architecture impact present",
        "policy impact present",
        "audit/provenance impact present",
        "rollback plan present",
        "ADR dependency present",
        "gate dependency present",
        "test evidence present",
        "no-go acknowledgement present",
        "approval status false",
    ]:
        assert item in checklist

    catalog = _text("docs/release/v02-workstream-request-template-catalog.md")
    for column in [
        "Workstream",
        "Template",
        "Required ADR",
        "Required gate",
        "Required evidence",
        "Current approval state",
        "Implementation allowed today",
        "Release blocker if violated",
    ]:
        assert column in catalog

    review_rules = _text("docs/release/v02-request-package-review-rules.md")
    for heading in [
        "## Request Completeness Review",
        "## Duplicate Handling",
        "## Evidence Sufficiency Review",
        "## Security Review",
        "## Architecture Review",
        "## Operator Review",
        "## ADR Dependency Review",
        "## Gate Dependency Review",
        "## Rejection Rules",
        "## No Direct Implementation Approval",
    ]:
        assert heading in review_rules

    no_go = _text("docs/release/v02-request-package-no-go.md")
    for condition in [
        "request package marks implementation approved",
        "proposal template marks implementation approved",
        "approval evidence marks approval true",
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

    adr = _text("docs/adr/0122-v02-implementation-request-pack.md")
    for required in [
        "Decision: add v0.2 implementation request pack.",
        "Decision: AION-131 does not approve implementation.",
        "Decision: request packs and proposal templates remain planning-only.",
        (
            "Decision: future implementation still requires explicit approval "
            "records, ADRs, and gate evidence."
        ),
        "Decision: no v0.2 release or tag is created.",
        (
            "Reason: AION needs a standard request pack before implementation "
            "proposals can be reviewed."
        ),
        (
            "Consequence: future workstreams must submit complete evidence "
            "before approval consideration."
        ),
        "Constraint: no runtime enablement.",
        "Constraint: no external calls.",
        "Constraint: no credentials/tokens.",
        "Constraint: no sandbox execution.",
        "Constraint: no privileged bypass.",
    ]:
        assert required in adr


def test_v02_request_pack_examples_are_safe() -> None:
    for relative in EXAMPLES:
        payload = _json(relative)
        assert payload["task_id"] == "AION-131"
        assert payload["status"] == "passed"
        assert payload["synthetic"] is True
        assert payload["v02_implementation_request_pack_created"] is True
        assert payload["proposal_templates_created"] is True
        assert payload["approval_evidence_boundary_created"] is True
        assert payload["request_pack_preview_only"] is True
        assert payload["proposal_registry_preview_only"] is True
        assert payload["approval_queue_preview_only"] is True
        _assert_false_keys(payload, relative)

    templates = _json("examples/release/v02-proposal-submission-template.json")
    assert len(templates["templates"]) == 10
    for template in templates["templates"]:
        for field in [
            "workstream",
            "problem_statement",
            "proposed_change",
            "runtime_capability_requested",
            "current_approval_state",
            "required_adr",
            "required_gate",
            "required_evidence",
            "security_impact",
            "policy_impact",
            "rollback_audit_plan",
            "default_approval_status",
        ]:
            assert field in template
        assert template["current_approval_state"] is False
        assert template["default_approval_status"] is False

    checklist = _json("examples/release/v02-implementation-request-evidence-checklist.json")
    assert {item["item"] for item in checklist["checklist"]} == {
        "problem statement present",
        "risk statement present",
        "security impact present",
        "architecture impact present",
        "policy impact present",
        "audit/provenance impact present",
        "rollback plan present",
        "ADR dependency present",
        "gate dependency present",
        "test evidence present",
        "no-go acknowledgement present",
        "approval status false",
    }
    assert all(item["present"] is True for item in checklist["checklist"])

    catalog = _json("examples/release/v02-workstream-request-template-catalog.json")
    assert len(catalog["catalog"]) == 10
    assert all(item["implementation_allowed_today"] is False for item in catalog["catalog"])

    for relative in EXAMPLES[-2:]:
        payload = _json(relative)
        assert payload["read_only"] is True
        assert payload["redaction_applied"] is True
        assert payload["sections"]
        assert payload["blockers"]
        assert payload["warnings"]
        assert payload["refs"]
        assert payload["forbidden_actions"]


def test_v02_request_pack_scripts_are_executable_and_pass() -> None:
    scripts = [
        ROOT / "scripts/v02-implementation-request-pack-check.sh",
        ROOT / "scripts/v02-request-pack-freeze.sh",
        ROOT / "scripts/v02-request-pack-no-go-regression.sh",
    ]
    for script in scripts:
        assert script.exists(), script
        assert script.stat().st_mode & stat.S_IXUSR, script
        subprocess.run(["bash", "-n", str(script)], cwd=ROOT, check=True)

    env = {
        **os.environ,
        "AION_V02_IMPLEMENTATION_REQUEST_PACK_SKIP_INHERITED_GATES": "1",
        "AION_V02_REQUEST_PACK_FREEZE_SKIP_FULL_CHECK": "1",
    }
    for command in [
        "./scripts/v02-implementation-request-pack-check.sh",
        "./scripts/v02-request-pack-freeze.sh",
        "./scripts/v02-request-pack-no-go-regression.sh",
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
                "implementation_approved",
                "approval_state",
                "default_approval_status",
                "implementation_allowed_today",
            }:
                assert nested is False, f"{context}.{key} must be false"
            _assert_false_keys(nested, f"{context}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _assert_false_keys(item, f"{context}[{index}]")
