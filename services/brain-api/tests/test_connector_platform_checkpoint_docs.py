"""AION-115 connector platform checkpoint regression tests."""

from __future__ import annotations

import json
import os
import stat
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]

DOCS = [
    "docs/connectors/connector-platform-checkpoint.md",
    "docs/connectors/connector-phase-evidence-pack.md",
    "docs/connectors/connector-safety-state-summary.md",
    "docs/connectors/connector-implementation-roadmap-freeze.md",
    "docs/connectors/connector-unresolved-risk-register.md",
    "docs/connectors/connector-future-work-decision-log.md",
    "docs/connectors/connector-phase-closeout-checklist.md",
    "docs/adr/0106-connector-platform-checkpoint.md",
]

EXAMPLES = [
    "examples/connectors/connector-platform-checkpoint.json",
    "examples/connectors/connector-phase-evidence-pack.json",
    "examples/connectors/connector-safety-state-summary.json",
    "examples/connectors/connector-implementation-roadmap-freeze.json",
    "examples/connectors/connector-phase-closeout-result.json",
    "operator-console-static/demo-data/connector-platform-checkpoint.json",
    "operator-console-static/demo-data/connector-phase-closeout.json",
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


def test_connector_platform_checkpoint_docs_exist_and_are_indexed() -> None:
    for relative in DOCS:
        assert (ROOT / relative).exists(), relative

    index = _text("docs/adr/README.md")
    assert "0106-connector-platform-checkpoint.md" in index

    checkpoint = _text("docs/connectors/connector-platform-checkpoint.md")
    for heading in [
        "## Purpose",
        "## Scope",
        "## AION-106 Through AION-114 Summary",
        "## Current Connector Safe State",
        "## Confirmed Disabled Capabilities",
        "## Evidence Scripts",
        "## Release Blockers",
        "## Checkpoint Decision",
        "## Next Phase Boundary",
    ]:
        assert heading in checkpoint

    adr = _text("docs/adr/0106-connector-platform-checkpoint.md")
    assert "Connector implementation remains unapproved" in adr
    assert "no runtime enablement" in adr
    assert "no external calls" in adr
    assert "no credentials/tokens" in adr
    assert "no sandbox execution" in adr


def test_connector_platform_checkpoint_examples_are_valid_and_safe() -> None:
    for relative in EXAMPLES:
        payload = _json(relative)
        if relative.startswith("examples/"):
            assert payload["synthetic"] is True
        assert payload["release_gate_passed"] is True
        assert payload["safety_freeze_passed"] is True
        _assert_false_keys(payload)
        _assert_no_blocked_strings(payload)


def test_connector_platform_checkpoint_scripts_are_executable_and_pass() -> None:
    scripts = [
        ("scripts/connector-platform-checkpoint.sh", "Connector platform checkpoint PASS"),
        ("scripts/connector-platform-freeze-check.sh", "Connector platform freeze PASS"),
    ]
    env = os.environ.copy()
    env["PYTEST_CURRENT_TEST"] = env.get(
        "PYTEST_CURRENT_TEST",
        "test_connector_platform_checkpoint_scripts_are_executable_and_pass (call)",
    )

    for relative, expected in scripts:
        script = ROOT / relative
        assert script.exists(), relative
        assert os.access(script, os.X_OK)
        assert script.stat().st_mode & stat.S_IXUSR
        result = subprocess.run(
            [str(script)],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
            env=env,
        )
        assert expected in result.stdout
        if relative == "scripts/connector-platform-freeze-check.sh":
            assert "PASS: full repository check deferred to outer gate" in result.stdout


def test_connector_platform_checkpoint_keeps_blocked_files_absent() -> None:
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
    candidates = ["origin/main", "main"]
    github_base_ref = os.environ.get("GITHUB_BASE_REF")
    if github_base_ref:
        candidates.append(f"origin/{github_base_ref}")
        candidates.append(github_base_ref)

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
