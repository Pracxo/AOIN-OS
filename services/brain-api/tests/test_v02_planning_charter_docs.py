"""AION-119 v0.2 planning charter regression tests."""

from __future__ import annotations

import json
import os
import stat
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]

DOCS = [
    "docs/release/v02-planning-charter.md",
    "docs/release/v02-runtime-implementation-decision-framework.md",
    "docs/release/v02-candidate-workstream-map.md",
    "docs/release/v02-adr-requirements.md",
    "docs/release/v02-gate-dependency-matrix.md",
    "docs/release/v02-no-go-planning-boundary.md",
    "docs/release/v02-backlog-intake-criteria.md",
    "docs/release/v02-planning-closeout-checklist.md",
    "docs/adr/0110-v02-planning-charter.md",
]

EXAMPLES = [
    "examples/release/v02-planning-charter.json",
    "examples/release/v02-runtime-decision-framework.json",
    "examples/release/v02-candidate-workstream-map.json",
    "examples/release/v02-gate-dependency-matrix.json",
    "examples/release/v02-backlog-intake-result.json",
    "operator-console-static/demo-data/v02-planning-charter.json",
    "operator-console-static/demo-data/v02-gate-dependency-matrix.json",
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
    "./scripts/v02-planning-charter-check.sh",
    "./scripts/v02-planning-no-go-regression.sh",
}


def test_v02_planning_docs_exist_and_are_indexed() -> None:
    for relative in DOCS:
        assert (ROOT / relative).exists(), relative

    index = _text("docs/adr/README.md")
    assert "0110-v02-planning-charter.md" in index

    charter = _text("docs/release/v02-planning-charter.md")
    for heading in [
        "## Purpose",
        "## Scope",
        "## v0.2 Planning Goals",
        "## Out-of-Scope Runtime Implementation",
        "## Required Decision Gates",
        "## Required ADRs",
        "## Required Evidence",
        "## Release Blocker Conditions",
        "## Planning Exit Criteria",
        "## No v0.2 Tag",
    ]:
        assert heading in charter

    framework = _text("docs/release/v02-runtime-implementation-decision-framework.md")
    for area in [
        "production auth",
        "operator write execution",
        "connector runtime",
        "connector credential store",
        "sandbox execution",
        "module activation",
        "external calls",
        "runtime route registration",
        "audit/provenance",
        "rollback",
        "operator review",
        "policy enforcement",
    ]:
        assert area in framework.lower()
    for column in [
        "Current Approval State",
        "Required ADR",
        "Required Gate",
        "Required Evidence",
        "No-Go Conditions",
    ]:
        assert column in framework

    workstreams = _text("docs/release/v02-candidate-workstream-map.md")
    for workstream in [
        "production auth implementation planning",
        "connector runtime implementation planning",
        "credential store implementation planning",
        "sandbox runtime implementation planning",
        "operator write execution planning",
        "module activation implementation planning",
        "external call release gate planning",
        "audit/provenance hardening",
        "rollback and recovery model",
        "static console to production UI decision",
    ]:
        assert workstream in workstreams
    assert "planning-only" in workstreams
    assert "implementation-unapproved" in workstreams

    adr_requirements = _text("docs/release/v02-adr-requirements.md")
    for adr in [
        "production auth implementation ADR",
        "connector runtime implementation ADR",
        "credential store implementation ADR",
        "sandbox runtime implementation ADR",
        "operator write execution ADR",
        "module activation ADR",
        "external calls release ADR",
        "rollback/audit ADR",
        "production UI decision ADR",
    ]:
        assert adr in adr_requirements

    matrix = _text("docs/release/v02-gate-dependency-matrix.md")
    for column in [
        "Workstream",
        "Required Prior Gates",
        "Required New Gates",
        "Required ADR",
        "Approved Today",
        "Blocked Until",
        "Release Blocker If Violated",
    ]:
        assert column in matrix

    no_go = _text("docs/release/v02-no-go-planning-boundary.md")
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
    ]:
        assert condition in no_go

    backlog = _text("docs/release/v02-backlog-intake-criteria.md")
    for required in [
        "planning-only intake format",
        "problem statement",
        "risk statement",
        "ADR dependency",
        "gate dependency",
        "no-go statement",
        "rollback/audit consideration",
        "security review",
        "owner",
        "Rejection Conditions",
    ]:
        assert required in backlog

    closeout = _text("docs/release/v02-planning-closeout-checklist.md")
    for item in [
        "docs complete",
        "examples valid",
        "scripts executable",
        "post-v0.1 release candidate gate passing",
        "platform integration gate passing",
        "connector platform gate passing",
        "operator platform gate passing",
        "no runtime implementation",
        "no v0.2 tag",
        "no external calls",
        "no credentials/tokens",
        "no sandbox execution",
        "no package files",
        "no migrations",
    ]:
        assert item in closeout

    adr = _text("docs/adr/0110-v02-planning-charter.md")
    assert "Decision: add v0.2 planning charter." in adr
    assert "Decision: AION-119 does not approve implementation." in adr
    assert "Decision: no v0.2 release or tag is created." in adr
    assert "Decision: future v0.2 implementation requires explicit ADRs and gate evidence." in adr
    assert "Reason: AION needs structured planning before runtime implementation." in adr
    assert "Consequence: v0.2 work is limited to gated planning until explicit approval." in adr
    assert "Constraint: no runtime enablement." in adr
    assert "Constraint: no external calls." in adr
    assert "Constraint: no credentials/tokens." in adr
    assert "Constraint: no sandbox execution." in adr
    assert "Constraint: no privileged bypass." in adr


def test_v02_planning_examples_are_valid_and_safe() -> None:
    for relative in EXAMPLES:
        payload = _json(relative)
        if relative.startswith("examples/"):
            assert payload["synthetic"] is True
        assert payload["status"] == "passed"
        assert payload["v02_planning_charter_created"] is True
        _assert_false_keys(payload)
        _assert_no_blocked_strings(payload)


def test_v02_planning_scripts_are_executable_and_wired() -> None:
    scripts = [
        (
            "scripts/v02-planning-charter-check.sh",
            "v0.2 planning charter check PASS",
        ),
        (
            "scripts/v02-planning-no-go-regression.sh",
            "v0.2 planning no-go regression PASS",
        ),
    ]
    for relative, expected in scripts:
        script = ROOT / relative
        assert script.exists(), relative
        assert os.access(script, os.X_OK)
        assert script.stat().st_mode & stat.S_IXUSR
        assert expected in script.read_text()

    charter = _text("scripts/v02-planning-charter-check.sh")
    for command in [
        "./scripts/post-v01-release-candidate-gate.sh",
        "./scripts/post-v01-release-candidate-freeze.sh",
        "./scripts/post-v01-release-candidate-no-go-regression.sh",
        "./scripts/platform-integration-checkpoint.sh",
        "./scripts/platform-integration-freeze-check.sh",
        "./scripts/platform-integration-no-go-regression.sh",
        "./scripts/docs-check.sh",
        "./scripts/final-docs-audit.sh",
        "./scripts/verify-no-domain-drift.sh",
        "./scripts/boundary-check.sh",
    ]:
        assert command in charter

    no_go = _text("scripts/v02-planning-no-go-regression.sh")
    assert "source \"$ROOT_DIR/scripts/lib/portable-search.sh\"" in no_go
    assert "comparison_base()" in no_go
    assert "origin/main" in no_go
    assert "GITHUB_BASE_REF" in no_go
    assert "HEAD~1" in no_go


def test_v02_planning_static_console_is_wired() -> None:
    html = _text("operator-console-static/index.html")
    app = _text("operator-console-static/app.js")
    nav = _json("examples/operator-console/static-console-navigation-map.json")

    for command in SAFE_COPY_COMMANDS:
        assert command in html
        assert command in app
        assert command in nav["safe_copy_commands"]

    assert "demo-data/v02-planning-charter.json" in app
    assert "demo-data/v02-gate-dependency-matrix.json" in app
    assert "v02-planning-charter" in html
    assert "v02-gate-dependency-matrix" in html
    assert "runtime_implementation_approved" in app
    assert "v02_release_created" in app
    assert "loadReleaseCandidatePanels" in app


def test_v02_planning_keeps_blocked_files_absent() -> None:
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
    changed: set[str] = set()
    base = _comparison_base()
    if base is not None:
        diff = subprocess.run(
            ["git", "diff", "--name-only", "--diff-filter=ACMRT", base, "HEAD"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        changed.update(line.strip() for line in diff.stdout.splitlines() if line.strip())

    for args in [
        ["diff", "--name-only", "--diff-filter=ACMRT"],
        ["diff", "--cached", "--name-only", "--diff-filter=ACMRT"],
        ["ls-files", "--others", "--exclude-standard"],
    ]:
        result = subprocess.run(
            ["git", *args],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        changed.update(line.strip() for line in result.stdout.splitlines() if line.strip())

    return changed
