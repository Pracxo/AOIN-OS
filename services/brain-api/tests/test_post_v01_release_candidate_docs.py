"""AION-118 post-v0.1 release candidate gate regression tests."""

from __future__ import annotations

import json
import os
import stat
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]

DOCS = [
    "docs/release/post-v01-release-candidate-gate.md",
    "docs/release/cross-phase-freeze-evidence.md",
    "docs/release/post-v01-release-candidate-checklist.md",
    "docs/release/v02-planning-boundary.md",
    "docs/release/implementation-approval-lock.md",
    "docs/release/post-v01-release-candidate-no-go.md",
    "docs/adr/0109-post-v01-release-candidate-gate.md",
]

EXAMPLES = [
    "examples/release/post-v01-release-candidate-gate.json",
    "examples/release/cross-phase-freeze-evidence.json",
    "examples/release/post-v01-release-candidate-checklist.json",
    "examples/release/v02-planning-boundary.json",
    "examples/release/implementation-approval-lock.json",
    "operator-console-static/demo-data/post-v01-release-candidate.json",
    "operator-console-static/demo-data/v02-planning-boundary.json",
]

FALSE_KEYS = {
    "operator_write_execution_approved",
    "connector_implementation_approved",
    "production_auth_approved",
    "module_activation_approved",
    "external_calls_approved",
    "credential_storage_approved",
    "token_storage_approved",
    "sandbox_execution_approved",
    "v02_tag_created",
    "v02_release_approved",
    "package_files_added",
    "migrations_added",
    "api_runtime_execution_route_added",
    "sdk_resource_implementation_added",
    "cli_command_implementation_added",
    "frontend_dependencies_added",
    "aion_v0_1_0_touched",
    "secrets_present",
    "credential_values_present",
    "token_values_present",
    "endpoints_present",
    "prompt_payloads_present",
    "private_reasoning_present",
    "implementation_allowed",
}

SAFE_COPY_COMMANDS = {
    "./scripts/post-v01-release-candidate-gate.sh",
    "./scripts/post-v01-release-candidate-freeze.sh",
    "./scripts/post-v01-release-candidate-no-go-regression.sh",
}


def test_release_candidate_docs_exist_and_are_indexed() -> None:
    for relative in DOCS:
        assert (ROOT / relative).exists(), relative

    index = _text("docs/adr/README.md")
    assert "0109-post-v01-release-candidate-gate.md" in index

    gate = _text("docs/release/post-v01-release-candidate-gate.md")
    for heading in [
        "## Purpose",
        "## Scope",
        "## Required Prior Gates",
        "## Operator Platform Evidence",
        "## Connector Platform Evidence",
        "## Platform Integration Evidence",
        "## Release Blocker Conditions",
        "## Pass/Fail Criteria",
        "## No v0.2 Tag",
    ]:
        assert heading in gate

    freeze = _text("docs/release/cross-phase-freeze-evidence.md")
    for evidence in [
        "operator platform regression",
        "operator platform freeze gate",
        "connector platform regression",
        "connector platform stabilization gate",
        "platform integration checkpoint",
        "platform integration freeze",
        "auth prototype review",
        "module activation design review",
        "static console safety",
        "docs and boundary checks",
    ]:
        assert evidence in freeze.lower()

    lock = _text("docs/release/implementation-approval-lock.md")
    for line in [
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
        assert line in lock

    adr = _text("docs/adr/0109-post-v01-release-candidate-gate.md")
    assert "Decision: add post-v0.1 release candidate gate." in adr
    assert "Decision: no v0.2 release or tag is created by AION-118." in adr
    assert "Decision: runtime implementation remains unapproved." in adr
    assert "Decision: future v0.2 work requires explicit planning and ADR gates." in adr
    assert "Reason" in adr
    assert "Constraint: no runtime enablement." in adr
    assert "Constraint: no external calls." in adr
    assert "Constraint: no credentials/tokens." in adr
    assert "Constraint: no sandbox execution." in adr
    assert "Constraint: no privileged bypass." in adr


def test_release_candidate_examples_are_valid_and_safe() -> None:
    for relative in EXAMPLES:
        payload = _json(relative)
        if relative.startswith("examples/"):
            assert payload["synthetic"] is True
        assert payload["status"] == "passed"
        assert payload["post_v01_release_candidate_passed"] is True
        _assert_false_keys(payload)
        _assert_no_blocked_strings(payload)


def test_release_candidate_scripts_are_executable_and_wired() -> None:
    scripts = [
        (
            "scripts/post-v01-release-candidate-gate.sh",
            "post-v0.1 release candidate gate PASS",
        ),
        (
            "scripts/post-v01-release-candidate-freeze.sh",
            "post-v0.1 release candidate freeze PASS",
        ),
        (
            "scripts/post-v01-release-candidate-no-go-regression.sh",
            "post-v0.1 release candidate no-go regression PASS",
        ),
    ]
    for relative, expected in scripts:
        script = ROOT / relative
        assert script.exists(), relative
        assert os.access(script, os.X_OK)
        assert script.stat().st_mode & stat.S_IXUSR
        assert expected in script.read_text()

    gate = _text("scripts/post-v01-release-candidate-gate.sh")
    for command in [
        "./scripts/platform-integration-checkpoint.sh",
        "./scripts/platform-integration-freeze-check.sh",
        "./scripts/platform-integration-no-go-regression.sh",
        "./scripts/operator-platform-regression.sh",
        "./scripts/operator-platform-freeze-gate.sh",
        "./scripts/connector-platform-regression.sh",
        "./scripts/connector-platform-stabilization-gate.sh",
        "./scripts/auth-prototype-review.sh",
        "./scripts/module-activation-design-review.sh",
        "./scripts/ui-release-gate.sh",
        "./scripts/static-console-safety-check.sh",
        "./scripts/docs-check.sh",
        "./scripts/final-docs-audit.sh",
        "./scripts/verify-no-domain-drift.sh",
        "./scripts/boundary-check.sh",
    ]:
        assert command in gate

    freeze = _text("scripts/post-v01-release-candidate-freeze.sh")
    assert "./scripts/check.sh" in freeze
    assert "PYTEST_CURRENT_TEST" in freeze
    assert "AION_AGGREGATE_GATE_RUNNING" in freeze
    assert "AION_CHECK_RUNNING" in freeze
    assert "PASS: full repository check deferred to outer gate" in freeze
    assert "aion-v0.1.0" in freeze
    assert "v0.2 tag must not exist" in freeze

    no_go = _text("scripts/post-v01-release-candidate-no-go-regression.sh")
    assert "source \"$ROOT_DIR/scripts/lib/portable-search.sh\"" in no_go
    assert "comparison_base()" in no_go
    assert "origin/main" in no_go
    assert "GITHUB_BASE_REF" in no_go
    assert "HEAD~1" in no_go


def test_release_candidate_static_console_is_wired() -> None:
    html = _text("operator-console-static/index.html")
    app = _text("operator-console-static/app.js")
    nav = _json("examples/operator-console/static-console-navigation-map.json")

    for command in SAFE_COPY_COMMANDS:
        assert command in html
        assert command in app
        assert command in nav["safe_copy_commands"]

    assert "demo-data/post-v01-release-candidate.json" in app
    assert "demo-data/v02-planning-boundary.json" in app
    assert "post-v01-release-candidate" in html
    assert "v02-planning-boundary" in html
    assert "loadReleaseCandidatePanels" in app
    assert "renderReleaseCandidateEvidence" in app


def test_release_candidate_keeps_blocked_files_absent() -> None:
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
