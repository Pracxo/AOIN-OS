"""AION-124 v0.2 workstream intake readiness regression tests."""

from __future__ import annotations

import json
import os
import stat
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]

DOCS = [
    "docs/release/v02-workstream-intake-readiness-gate.md",
    "docs/release/v02-workstream-intake-evidence-pack.md",
    "docs/release/v02-approval-record-evidence-pack.md",
    "docs/release/v02-implementation-sequencing-freeze.md",
    "docs/release/v02-workstream-readiness-scorecard.md",
    "docs/release/v02-workstream-rejection-rules.md",
    "docs/release/v02-workstream-intake-no-go.md",
    "docs/adr/0115-v02-workstream-intake-readiness.md",
]

EXAMPLES = [
    "examples/release/v02-workstream-intake-readiness-gate.json",
    "examples/release/v02-workstream-intake-evidence-pack.json",
    "examples/release/v02-approval-record-evidence-pack.json",
    "examples/release/v02-implementation-sequencing-freeze.json",
    "examples/release/v02-workstream-readiness-scorecard.json",
    "operator-console-static/demo-data/v02-workstream-intake-readiness.json",
    "operator-console-static/demo-data/v02-implementation-sequencing-freeze.json",
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
    "approval_workflow_bypassed",
    "approval_record_missing",
    "adr_dependency_bypassed",
    "gate_dependency_bypassed",
    "approval_expiry_bypassed",
    "approval_revocation_bypassed",
    "dual_control_bypassed",
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


def test_v02_workstream_intake_docs_exist_and_are_indexed() -> None:
    for relative in DOCS:
        assert (ROOT / relative).exists(), relative

    index = _text("docs/adr/README.md")
    assert "0115-v02-workstream-intake-readiness.md" in index

    gate = _text("docs/release/v02-workstream-intake-readiness-gate.md")
    for heading in [
        "## Purpose",
        "## Scope",
        "## Required Prior Gates",
        "## Workstream Intake Evidence",
        "## Approval Record Evidence",
        "## Sequencing Evidence",
        "## Rejection Evidence",
        "## Implementation Approval Guard Checks",
        "## No-Go Conditions",
        "## No v0.2 Tag Or Release",
    ]:
        assert heading in gate
    assert "AION-124 explicitly creates no v0.2 tag and no release" in gate

    intake = _text("docs/release/v02-workstream-intake-evidence-pack.md")
    for required in [
        "implementation kickoff boundary",
        "approval workflow stabilization",
        "implementation request template",
        "approval decision record",
        "expiry and revocation model",
        "dual-control review model",
        "readiness final review",
        "planning stabilization gate",
        "post-v0.1 release candidate gate",
        "platform integration checkpoint",
        "docs and boundary checks",
    ]:
        assert required in intake

    approval = _text("docs/release/v02-approval-record-evidence-pack.md")
    for required in [
        "## Required ADR Evidence",
        "## Required Gate Evidence",
        "## Required Security Review Evidence",
        "## Required Architecture Review Evidence",
        "## Required Operator Review Evidence",
        "## Required Rollback/Audit Evidence",
        "Default approval status: false.",
        "## Approval Expiry Status",
        "## Revocation Path",
        "## No-Go Result",
    ]:
        assert required in approval

    freeze = _text("docs/release/v02-implementation-sequencing-freeze.md")
    for required in [
        "## Sequencing Is Planning-Only",
        "## Implementation Sequencing Does Not Approve Implementation",
        "## Production Auth Planning Dependency",
        "## Audit/Provenance Hardening Planning",
        "## Rollback/Recovery Planning",
        "## Connector Runtime Locked",
        "## Credential Store Locked",
        "## Sandbox Runtime Locked",
        "## Operator Write Execution Locked",
        "## Module Activation Locked",
        "## Production UI Undecided",
    ]:
        assert required in freeze

    scorecard = _text("docs/release/v02-workstream-readiness-scorecard.md")
    for workstream in [
        "production auth implementation planning",
        "audit/provenance hardening planning",
        "rollback/recovery planning",
        "external call release gate planning",
        "connector runtime implementation planning",
        "credential store implementation planning",
        "sandbox runtime implementation planning",
        "operator write execution planning",
        "module activation implementation planning",
        "production UI decision planning",
    ]:
        assert workstream in scorecard
    for column in [
        "Readiness Score",
        "Approval State",
        "Required ADR",
        "Required Gate",
        "Blocker",
        "Next Planning Action",
        "Implementation Allowed Today",
    ]:
        assert column in scorecard
    assert "Implementation allowed today: false" in scorecard

    rejection = _text("docs/release/v02-workstream-rejection-rules.md")
    for condition in [
        "missing problem statement",
        "missing risk statement",
        "missing ADR dependency",
        "missing gate dependency",
        "missing rollback/audit consideration",
        "missing security review",
        "runtime enablement requested without ADR",
        "external call requested without release gate",
        "credential/token storage requested without credential store ADR",
        "sandbox execution requested without sandbox runtime ADR",
        "implementation approval requested directly",
        "package/migration/runtime route requested prematurely",
    ]:
        assert condition in rejection

    no_go = _text("docs/release/v02-workstream-intake-no-go.md")
    for condition in [
        "implementation approval set true",
        "backlog implementation approval set true",
        "workstream marked implementation approved",
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

    adr = _text("docs/adr/0115-v02-workstream-intake-readiness.md")
    assert "Decision: add v0.2 workstream intake readiness gate." in adr
    assert "Decision: AION-124 does not approve implementation." in adr
    assert "Decision: sequencing and intake remain planning-only." in adr
    assert "Decision: future implementation requires explicit approval records, ADRs," in adr
    assert "Decision: no v0.2 release or tag is created." in adr
    assert "Reason: AION needs a stable intake boundary before implementation" in adr
    assert "Consequence: future runtime work must pass intake, evidence, sequencing," in adr
    assert "Constraint: no runtime enablement." in adr
    assert "Constraint: no external calls." in adr
    assert "Constraint: no credentials/tokens." in adr
    assert "Constraint: no sandbox execution." in adr
    assert "Constraint: no privileged bypass." in adr


def test_v02_workstream_intake_examples_are_safe() -> None:
    for relative in EXAMPLES:
        payload = _json(relative)
        if relative.startswith("examples/"):
            assert payload["synthetic"] is True
        assert payload["status"] == "passed"
        assert payload["task_id"] == "AION-124"
        assert payload["v02_workstream_intake_ready"] is True
        _assert_false_keys(payload, relative)


def test_v02_workstream_intake_scripts_are_executable_and_pass() -> None:
    for script in [
        ROOT / "scripts/v02-workstream-intake-readiness-gate.sh",
        ROOT / "scripts/v02-workstream-intake-freeze.sh",
        ROOT / "scripts/v02-workstream-intake-no-go-regression.sh",
    ]:
        assert script.exists()
        assert os.access(script, os.X_OK)
        assert script.stat().st_mode & stat.S_IXUSR

    env = os.environ.copy()
    env["AION_V02_WORKSTREAM_INTAKE_SKIP_NESTED_GATES"] = "1"
    env["AION_V02_WORKSTREAM_INTAKE_FREEZE_SKIP_FULL_CHECK"] = "1"
    subprocess.run(
        ["./scripts/v02-workstream-intake-readiness-gate.sh"],
        cwd=ROOT,
        env=env,
        check=True,
    )
    subprocess.run(
        ["./scripts/v02-workstream-intake-freeze.sh"],
        cwd=ROOT,
        env=env,
        check=True,
    )
    subprocess.run(
        ["./scripts/v02-workstream-intake-no-go-regression.sh"],
        cwd=ROOT,
        check=True,
    )


def _text(relative: str) -> str:
    return (ROOT / relative).read_text()


def _json(relative: str) -> dict[str, Any]:
    return json.loads(_text(relative))


def _assert_false_keys(value: Any, context: str) -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            if key in FALSE_KEYS:
                assert nested is False, f"{context}.{key} must be false"
            _assert_false_keys(nested, f"{context}.{key}")
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            _assert_false_keys(nested, f"{context}[{index}]")
