"""AION-116 connector platform stabilization regression tests."""

from __future__ import annotations

import json
import os
import stat
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]

DOCS = [
    "docs/connectors/connector-platform-stabilization-runbook.md",
    "docs/connectors/connector-long-running-regression-matrix.md",
    "docs/connectors/connector-phase-freeze-gate.md",
    "docs/connectors/connector-stabilization-evidence-pack.md",
    "docs/connectors/connector-safety-baseline-lock.md",
    "docs/connectors/connector-regression-evidence.md",
    "docs/adr/0107-connector-platform-stabilization-gate.md",
]

EXAMPLES = [
    "examples/connectors/connector-platform-stabilization-result.json",
    "examples/connectors/connector-long-running-regression-matrix.json",
    "examples/connectors/connector-phase-freeze-gate-result.json",
    "examples/connectors/connector-stabilization-evidence-pack.json",
    "operator-console-static/demo-data/connector-platform-stabilization.json",
    "operator-console-static/demo-data/connector-phase-freeze-gate.json",
]

FALSE_KEYS = {
    "connector_runtime_enabled",
    "external_calls_enabled",
    "credentials_present",
    "token_storage_enabled",
    "sandbox_execution_enabled",
    "connector_activation_enabled",
    "route_registration_enabled",
    "implementation_approved",
    "package_files_added",
    "migrations_added",
    "provider_sdk_dependency_added",
    "api_runtime_execution_route_added",
    "endpoint_references_present",
    "secret_material_present",
    "credential_values_present",
    "token_values_present",
    "private_prompt_material_present",
    "private_reasoning_present",
    "runtime_approval",
}


def test_connector_platform_stabilization_docs_exist_and_are_indexed() -> None:
    for relative in DOCS:
        assert (ROOT / relative).exists(), relative

    index = _text("docs/adr/README.md")
    assert "0107-connector-platform-stabilization-gate.md" in index

    runbook = _text("docs/connectors/connector-platform-stabilization-runbook.md")
    for heading in [
        "## Purpose",
        "## Scope",
        "## Required Connector Gates",
        "## Stabilization Workflow",
        "## CI Workflow",
        "## Manual Verification Workflow",
        "## Failure Triage",
        "## Rollback Path",
        "## Release Blocker Conditions",
        "## No-Go Conditions",
    ]:
        assert heading in runbook

    freeze = _text("docs/connectors/connector-phase-freeze-gate.md")
    assert "implementation approval false" in freeze
    assert "runtime disabled" in freeze
    assert "external calls absent" in freeze
    assert "credentials/tokens absent" in freeze
    assert "sandbox execution absent" in freeze
    assert "future ADR required" in freeze

    adr = _text("docs/adr/0107-connector-platform-stabilization-gate.md")
    assert "Decision: add connector platform stabilization gate." in adr
    assert "Decision: connector phase remains frozen after AION-116." in adr
    assert "Decision: connector implementation remains unapproved." in adr
    assert "Constraint: no runtime enablement." in adr
    assert "Constraint: no external calls." in adr
    assert "Constraint: no credentials/tokens." in adr
    assert "Constraint: no sandbox execution." in adr


def test_connector_platform_stabilization_examples_are_valid_and_safe() -> None:
    for relative in EXAMPLES:
        payload = _json(relative)
        if relative.startswith("examples/"):
            assert payload["synthetic"] is True
        assert payload["release_gate_passed"] is True
        assert payload["checkpoint_passed"] is True
        assert payload["stabilization_gate_passed"] is True
        _assert_false_keys(payload)
        _assert_no_blocked_strings(payload)


def test_connector_platform_stabilization_scripts_are_executable_and_wired() -> None:
    scripts = [
        ("scripts/connector-platform-regression.sh", "connector platform regression PASS"),
        (
            "scripts/connector-platform-stabilization-gate.sh",
            "connector platform stabilization gate PASS",
        ),
    ]
    for relative, expected in scripts:
        script = ROOT / relative
        assert script.exists(), relative
        assert os.access(script, os.X_OK)
        assert script.stat().st_mode & stat.S_IXUSR
        text = script.read_text()
        assert expected in text

    regression = _text("scripts/connector-platform-regression.sh")
    for command in [
        "./scripts/connector-platform-checkpoint.sh",
        "./scripts/connector-platform-freeze-check.sh",
        "./scripts/connector-release-gate.sh",
        "./scripts/connector-safety-freeze.sh",
        "./scripts/connector-release-no-go-regression.sh",
        "./scripts/connector-runtime-review.sh",
        "./scripts/connector-runtime-no-external-call-regression.sh",
        "./scripts/connector-simulator-check.sh",
        "./scripts/connector-simulator-no-go-regression.sh",
        "./scripts/connector-policy-check.sh",
        "./scripts/connector-policy-no-go-regression.sh",
        "./scripts/connector-sandbox-check.sh",
        "./scripts/connector-sandbox-no-go-regression.sh",
        "./scripts/connector-credential-check.sh",
        "./scripts/connector-credential-no-go-regression.sh",
        "./scripts/docs-check.sh",
        "./scripts/final-docs-audit.sh",
        "./scripts/verify-no-domain-drift.sh",
        "./scripts/boundary-check.sh",
    ]:
        assert command in regression

    gate = _text("scripts/connector-platform-stabilization-gate.sh")
    assert "./scripts/connector-platform-regression.sh" in gate
    assert "./scripts/check.sh" in gate
    assert "PYTEST_CURRENT_TEST" in gate
    assert "AION_AGGREGATE_GATE_RUNNING" in gate
    assert "AION_CHECK_RUNNING" in gate
    assert "PASS: full repository check deferred to outer gate" in gate
    assert "aion-v0.1.0" in gate


def test_connector_platform_stabilization_keeps_blocked_files_absent() -> None:
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
    return (
        subprocess.run(
            ["git", "rev-parse", "--verify", "--quiet", ref],
            cwd=ROOT,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        ).returncode
        == 0
    )


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

    untracked = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    changed.update(line.strip() for line in untracked.stdout.splitlines() if line.strip())
    return changed
