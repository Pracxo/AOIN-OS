"""AION-121 v0.2 readiness final review regression tests."""

from __future__ import annotations

import json
import os
import stat
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]

DOCS = [
    "docs/release/v02-readiness-final-review.md",
    "docs/release/v02-planning-phase-closeout-report.md",
    "docs/release/v02-implementation-approval-guard.md",
    "docs/release/v02-readiness-evidence-matrix.md",
    "docs/release/v02-blocked-implementation-summary.md",
    "docs/release/v02-final-no-go-review.md",
    "docs/release/v02-readiness-final-checklist.md",
    "docs/adr/0112-v02-readiness-final-review.md",
]

EXAMPLES = [
    "examples/release/v02-readiness-final-review.json",
    "examples/release/v02-planning-phase-closeout-report.json",
    "examples/release/v02-implementation-approval-guard.json",
    "examples/release/v02-readiness-evidence-matrix.json",
    "examples/release/v02-final-no-go-review.json",
    "operator-console-static/demo-data/v02-readiness-final-review.json",
    "operator-console-static/demo-data/v02-implementation-approval-guard.json",
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


def test_v02_readiness_final_docs_exist_and_are_indexed() -> None:
    for relative in DOCS:
        assert (ROOT / relative).exists(), relative

    index = _text("docs/adr/README.md")
    assert "0112-v02-readiness-final-review.md" in index

    review = _text("docs/release/v02-readiness-final-review.md")
    for heading in [
        "## Purpose",
        "## Scope",
        "## Planning Phase Status",
        "## Readiness Evidence",
        "## Implementation Approval Status",
        "## Blocked Runtime Areas",
        "## Remaining Risks",
        "## Required Future ADRs",
        "## Final Review Decision",
        "## No v0.2 Tag Or Release",
    ]:
        assert heading in review
    assert "AION-121 explicitly creates no v0.2 tag and no release" in review

    closeout = _text("docs/release/v02-planning-phase-closeout-report.md")
    for required in [
        "## AION-119 Summary",
        "## AION-120 Summary",
        "## Planning Artifacts Completed",
        "## Governance Boundary Completed",
        "## Backlog Intake Boundary Completed",
        "## No-Go Regression Status",
        "## Evidence Scripts",
        "## Closeout Decision",
    ]:
        assert required in closeout

    guard = _text("docs/release/v02-implementation-approval-guard.md")
    for required in [
        "runtime_implementation_approved=false",
        "backlog_implementation_items_approved=false",
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

    matrix = _text("docs/release/v02-readiness-evidence-matrix.md")
    for column in [
        "Area",
        "Evidence source",
        "Gate script",
        "Expected safe value",
        "Approval status",
        "Release blocker if violated",
        "Notes",
    ]:
        assert column in matrix

    blocked = _text("docs/release/v02-blocked-implementation-summary.md")
    for item in [
        "production auth implementation",
        "connector runtime implementation",
        "credential store implementation",
        "sandbox runtime implementation",
        "operator write execution",
        "module activation",
        "external calls",
        "runtime route registration",
        "package dependency additions",
        "migrations",
        "production UI implementation",
    ]:
        assert item in blocked
    for column in [
        "Blocked reason",
        "Required ADR",
        "Required gate",
        "Required security evidence",
        "Unblock condition",
    ]:
        assert column in blocked

    no_go = _text("docs/release/v02-final-no-go-review.md")
    for condition in [
        "v0.2 tag created",
        "v0.2 release created",
        "implementation approval set true",
        "backlog implementation item approved",
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

    checklist = _text("docs/release/v02-readiness-final-checklist.md")
    for item in [
        "docs complete",
        "examples valid",
        "scripts executable",
        "v0.2 planning charter passing",
        "v0.2 planning stabilization passing",
        "post-v0.1 release candidate passing",
        "platform integration passing",
        "implementation approval guard passing",
        "no runtime implementation",
        "no v0.2 tag",
        "no v0.2 release",
        "no external calls",
        "no credentials/tokens",
        "no sandbox execution",
    ]:
        assert item in checklist

    adr = _text("docs/adr/0112-v02-readiness-final-review.md")
    assert "Decision: add v0.2 readiness final review." in adr
    assert "Decision: v0.2 planning phase closeout is evidence-only." in adr
    assert "Decision: implementation approval remains false." in adr
    assert "Decision: backlog implementation approval remains false." in adr
    assert "Decision: no v0.2 release or tag is created." in adr
    assert "Constraint: no runtime enablement." in adr
    assert "Constraint: no external calls." in adr
    assert "Constraint: no credentials/tokens." in adr
    assert "Constraint: no sandbox execution." in adr


def test_v02_readiness_final_examples_are_safe() -> None:
    for relative in EXAMPLES:
        payload = _json(relative)
        if relative.startswith("examples/"):
            assert payload["synthetic"] is True
        assert payload["status"] == "passed"
        assert payload["task_id"] == "AION-121"
        assert payload["v02_readiness_final_review_passed"] is True
        assert payload["v02_planning_phase_closed"] is True
        _assert_false_keys(payload, relative)


def test_v02_readiness_final_scripts_are_executable_and_pass() -> None:
    for script in [
        ROOT / "scripts/v02-readiness-final-review.sh",
        ROOT / "scripts/v02-readiness-final-freeze.sh",
        ROOT / "scripts/v02-readiness-final-no-go-regression.sh",
    ]:
        assert script.exists()
        assert script.stat().st_mode & stat.S_IXUSR

    env = os.environ.copy()
    env["AION_V02_READINESS_FINAL_REVIEW_SKIP_NESTED_GATES"] = "1"
    env["AION_V02_READINESS_FINAL_FREEZE_SKIP_FULL_CHECK"] = "1"
    subprocess.run(
        ["./scripts/v02-readiness-final-review.sh"],
        cwd=ROOT,
        env=env,
        check=True,
    )
    subprocess.run(
        ["./scripts/v02-readiness-final-freeze.sh"],
        cwd=ROOT,
        env=env,
        check=True,
    )
    subprocess.run(
        ["./scripts/v02-readiness-final-no-go-regression.sh"],
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
