"""AION-120 v0.2 planning stabilization regression tests."""

from __future__ import annotations

import json
import os
import stat
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]

DOCS = [
    "docs/release/v02-planning-stabilization-gate.md",
    "docs/release/v02-backlog-governance-freeze.md",
    "docs/release/v02-implementation-readiness-scorecard.md",
    "docs/release/v02-planning-evidence-pack.md",
    "docs/release/v02-decision-review-calendar.md",
    "docs/release/v02-blocked-work-register.md",
    "docs/release/v02-planning-stabilization-no-go.md",
    "docs/adr/0111-v02-planning-stabilization-gate.md",
]

EXAMPLES = [
    "examples/release/v02-planning-stabilization-gate.json",
    "examples/release/v02-backlog-governance-freeze.json",
    "examples/release/v02-implementation-readiness-scorecard.json",
    "examples/release/v02-planning-evidence-pack.json",
    "examples/release/v02-blocked-work-register.json",
    "operator-console-static/demo-data/v02-planning-stabilization.json",
    "operator-console-static/demo-data/v02-implementation-readiness-scorecard.json",
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

SAFE_COPY_COMMANDS = {
    "./scripts/v02-planning-stabilization-gate.sh",
    "./scripts/v02-planning-freeze-check.sh",
    "./scripts/v02-planning-stabilization-no-go-regression.sh",
}


def test_v02_planning_stabilization_docs_exist_and_are_indexed() -> None:
    for relative in DOCS:
        assert (ROOT / relative).exists(), relative

    index = _text("docs/adr/README.md")
    assert "0111-v02-planning-stabilization-gate.md" in index

    gate = _text("docs/release/v02-planning-stabilization-gate.md")
    for heading in [
        "## Purpose",
        "## Scope",
        "## Required Prior Gates",
        "## Planning Charter Evidence",
        "## Backlog Governance Evidence",
        "## ADR Dependency Evidence",
        "## Gate Dependency Evidence",
        "## Implementation Approval Lock Checks",
        "## Release Blocker Conditions",
        "## Pass/Fail Criteria",
        "## No v0.2 Tag Or Release",
    ]:
        assert heading in gate
    assert "creates no v0.2 tag and no release" in gate

    backlog = _text("docs/release/v02-backlog-governance-freeze.md")
    for required in [
        "Planning-Only Backlog Rules",
        "Accepted Intake Fields",
        "Rejected Intake Conditions",
        "Required ADR Mapping",
        "Required Gate Mapping",
        "Security Review Requirement",
        "Rollback And Audit Requirement",
        "Implementation Approval Remains False",
        "No-Go Conditions",
    ]:
        assert required in backlog

    scorecard = _text("docs/release/v02-implementation-readiness-scorecard.md")
    for area in [
        "production auth",
        "operator write execution",
        "connector runtime",
        "credential store",
        "sandbox runtime",
        "module activation",
        "external calls",
        "runtime route registration",
        "audit/provenance",
        "rollback",
        "production UI decision",
    ]:
        assert area in scorecard
    for column in [
        "Current Status",
        "Approval State",
        "Required ADR",
        "Required Gate",
        "Readiness Score",
        "Blocker",
        "Next Planning Action",
    ]:
        assert column in scorecard

    evidence = _text("docs/release/v02-planning-evidence-pack.md")
    for source in [
        "v0.2 planning charter",
        "runtime decision framework",
        "candidate workstream map",
        "ADR requirements",
        "gate dependency matrix",
        "backlog intake criteria",
        "no-go planning boundary",
        "post-v0.1 release candidate gate",
        "platform integration checkpoint",
        "docs and boundary checks",
    ]:
        assert source in evidence

    calendar = _text("docs/release/v02-decision-review-calendar.md")
    for required in [
        "Decision Review Cadence",
        "Required Attendees And Roles",
        "Decision Inputs",
        "Review Outputs",
        "Approval Restrictions",
        "ADR Creation Requirements",
        "Gate Evidence Requirements",
        "No-Go Triggers",
    ]:
        assert required in calendar

    blocked = _text("docs/release/v02-blocked-work-register.md")
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
        "Reason Blocked",
        "Required ADR",
        "Required Gate",
        "Required Evidence",
        "Owner Placeholder",
        "Unblock Condition",
    ]:
        assert column in blocked

    no_go = _text("docs/release/v02-planning-stabilization-no-go.md")
    for condition in [
        "v0.2 tag created",
        "v0.2 release created",
        "implementation approval set true",
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
        "backlog item marked implementation-approved",
    ]:
        assert condition in no_go

    adr = _text("docs/adr/0111-v02-planning-stabilization-gate.md")
    assert "Decision: add v0.2 planning stabilization gate." in adr
    assert "Decision: v0.2 remains planning-only after AION-120." in adr
    assert "Decision: implementation approval remains false." in adr
    assert "Decision: no v0.2 release or tag is created." in adr
    assert "future implementation requires explicit ADRs, gate evidence, and" in adr
    assert "Reason: AION needs stable v0.2 planning governance before implementation work." in adr
    assert "Consequence: v0.2 work remains constrained to approved planning backlog items." in adr
    assert "Constraint: no runtime enablement." in adr
    assert "Constraint: no external calls." in adr
    assert "Constraint: no credentials/tokens." in adr
    assert "Constraint: no sandbox execution." in adr
    assert "Constraint: no privileged bypass." in adr


def test_v02_planning_stabilization_examples_are_valid_and_safe() -> None:
    for relative in EXAMPLES:
        payload = _json(relative)
        if relative.startswith("examples/"):
            assert payload["synthetic"] is True
        assert payload["status"] == "passed"
        assert payload["v02_planning_stabilized"] is True
        _assert_false_keys(payload)
        _assert_no_blocked_strings(payload)


def test_v02_planning_stabilization_scripts_are_executable_and_wired() -> None:
    scripts = [
        (
            "scripts/v02-planning-stabilization-gate.sh",
            "v0.2 planning stabilization gate PASS",
        ),
        (
            "scripts/v02-planning-freeze-check.sh",
            "v0.2 planning freeze PASS",
        ),
        (
            "scripts/v02-planning-stabilization-no-go-regression.sh",
            "v0.2 planning stabilization no-go regression PASS",
        ),
    ]
    for relative, expected in scripts:
        script = ROOT / relative
        assert script.exists(), relative
        assert os.access(script, os.X_OK)
        assert script.stat().st_mode & stat.S_IXUSR
        assert expected in script.read_text()

    gate = _text("scripts/v02-planning-stabilization-gate.sh")
    for command in [
        "./scripts/v02-planning-charter-check.sh",
        "./scripts/v02-planning-no-go-regression.sh",
        "./scripts/post-v01-release-candidate-gate.sh",
        "./scripts/post-v01-release-candidate-freeze.sh",
        "./scripts/platform-integration-checkpoint.sh",
        "./scripts/platform-integration-freeze-check.sh",
        "./scripts/docs-check.sh",
        "./scripts/final-docs-audit.sh",
        "./scripts/verify-no-domain-drift.sh",
        "./scripts/boundary-check.sh",
    ]:
        assert command in gate

    freeze = _text("scripts/v02-planning-freeze-check.sh")
    assert "is_nested_gate_context()" in freeze
    assert "AION_V02_PLANNING_FREEZE_SKIP_FULL_CHECK" in freeze
    assert "./scripts/check.sh" in freeze
    assert "aion-v0.1.0" in freeze

    no_go = _text("scripts/v02-planning-stabilization-no-go-regression.sh")
    assert "source \"$ROOT_DIR/scripts/lib/portable-search.sh\"" in no_go
    assert "comparison_base()" in no_go
    assert "origin/main" in no_go
    assert "GITHUB_BASE_REF" in no_go
    assert "HEAD~1" in no_go


def test_v02_planning_stabilization_static_console_is_wired() -> None:
    html = _text("operator-console-static/index.html")
    app = _text("operator-console-static/app.js")
    nav = _json("examples/operator-console/static-console-navigation-map.json")

    for command in SAFE_COPY_COMMANDS:
        assert command in html
        assert command in app
        assert command in nav["safe_copy_commands"]

    assert "demo-data/v02-planning-stabilization.json" in app
    assert "demo-data/v02-implementation-readiness-scorecard.json" in app
    assert "v02-planning-stabilization" in html
    assert "v02-implementation-readiness-scorecard" in html
    assert "v02_planning_stabilized" in app
    assert "backlog_implementation_items_approved" in app
    assert "loadReleaseCandidatePanels" in app


def test_v02_planning_stabilization_keeps_blocked_files_absent() -> None:
    changed = _changed_files()
    blocked_names = {
        "package.json",
        "package-lock.json",
        "pnpm-lock.yaml",
        "yarn.lock",
        "bun.lockb",
    }
    assert not any(Path(name).name in blocked_names for name in changed)
    assert not any("migrations" in Path(name).parts for name in changed)
    assert not any(name.startswith("services/brain-api/src/aion_brain/api/") for name in changed)
    assert not any(
        name.startswith("packages/aion-sdk-python/src/aion_sdk/resources/") for name in changed
    )
    assert not any(
        name.startswith("packages/aion-sdk-python/src/aion_sdk/cli/commands/") for name in changed
    )


def _assert_false_keys(value: object) -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            if key in FALSE_KEYS:
                assert nested is False, key
            _assert_false_keys(nested)
    elif isinstance(value, list):
        for item in value:
            _assert_false_keys(item)


def _assert_no_blocked_strings(value: object) -> None:
    blocked = (
        "http://",
        "https://",
        "sk-",
        "ghp_",
        "xoxb-",
        "-----BEGIN PRIVATE KEY-----",
        "bearer ",
        "basic ",
        "api_key",
        "private_key",
        "access_token",
        "refresh_token",
        "id_token",
        "client_secret",
        "raw_prompt",
        "hidden_reasoning",
        "chain_of_thought",
    )
    if isinstance(value, dict):
        for nested in value.values():
            _assert_no_blocked_strings(nested)
    elif isinstance(value, list):
        for item in value:
            _assert_no_blocked_strings(item)
    elif isinstance(value, str):
        lowered = value.lower()
        for marker in blocked:
            assert marker not in lowered


def _json(relative: str) -> dict[str, Any]:
    return json.loads((ROOT / relative).read_text())


def _text(relative: str) -> str:
    return (ROOT / relative).read_text()


def _git_ref_exists(ref: str) -> bool:
    return subprocess.run(
        ["git", "rev-parse", "--verify", "--quiet", ref],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    ).returncode == 0


def _comparison_base() -> str | None:
    candidates: list[str] = []
    github_base_ref = os.environ.get("GITHUB_BASE_REF")
    if github_base_ref:
        candidates.extend([f"origin/{github_base_ref}", github_base_ref])
    candidates.extend(["origin/main", "main"])
    for candidate in candidates:
        if not _git_ref_exists(candidate):
            continue
        merge_base = subprocess.run(
            ["git", "merge-base", "HEAD", candidate],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        if merge_base.returncode == 0 and merge_base.stdout.strip():
            return merge_base.stdout.strip()
    if _git_ref_exists("HEAD~1"):
        return "HEAD~1"
    return None


def _changed_files() -> set[str]:
    base = _comparison_base()
    changed: set[str] = set()
    if base is not None:
        diff = subprocess.run(
            ["git", "diff", "--name-only", "--diff-filter=ACMRT", base, "HEAD"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        changed.update(line.strip() for line in diff.stdout.splitlines() if line.strip())
    for args in [
        ["git", "diff", "--name-only", "--diff-filter=ACMRT"],
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMRT"],
        ["git", "ls-files", "--others", "--exclude-standard"],
    ]:
        result = subprocess.run(
            args,
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        changed.update(line.strip() for line in result.stdout.splitlines() if line.strip())
    return changed
