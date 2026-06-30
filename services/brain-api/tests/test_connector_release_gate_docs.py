"""AION-114 connector release gate regression tests."""

from __future__ import annotations

import json
import os
import stat
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]

DOCS = [
    "docs/connectors/connector-release-gate.md",
    "docs/connectors/connector-safety-freeze.md",
    "docs/connectors/end-to-end-connector-readiness-evidence.md",
    "docs/connectors/connector-release-evidence-matrix.md",
    "docs/connectors/connector-implementation-readiness-decision.md",
    "docs/connectors/connector-release-no-go.md",
    "docs/adr/0105-connector-release-gate.md",
]

EXAMPLES = [
    "examples/connectors/connector-release-gate-result.json",
    "examples/connectors/connector-safety-freeze-result.json",
    "examples/connectors/end-to-end-connector-readiness-evidence.json",
    "examples/connectors/connector-release-evidence-matrix.json",
    "examples/connectors/connector-implementation-readiness-decision.json",
    "operator-console-static/demo-data/connector-release-gate.json",
    "operator-console-static/demo-data/connector-safety-freeze.json",
]

FALSE_KEYS = {
    "connector_runtime_enabled",
    "external_calls_enabled",
    "credentials_present",
    "token_storage_enabled",
    "sandbox_execution_enabled",
    "connector_activation_enabled",
    "route_registration_enabled",
    "package_files_added",
    "migrations_added",
    "implementation_approved",
    "provider_sdk_dependency_added",
    "api_runtime_execution_route_added",
    "endpoint_references_present",
}


def test_connector_release_gate_docs_exist_and_are_indexed() -> None:
    for relative in DOCS:
        assert (ROOT / relative).exists(), relative

    index = _text("docs/adr/README.md")
    assert "0105-connector-release-gate.md" in index

    gate = _text("docs/connectors/connector-release-gate.md")
    for heading in [
        "## Purpose",
        "## Scope",
        "## Required Prior Gates",
        "## Connector Runtime Disabled Checks",
        "## External Call Absence Checks",
        "## Credential/Token Absence Checks",
        "## Sandbox Execution Absence Checks",
        "## Policy Denial Checks",
        "## Dry-Run Simulator Checks",
        "## Static Console Checks",
        "## Documentation Checks",
        "## Release Blocker Conditions",
        "## Pass/Fail Criteria",
    ]:
        assert heading in gate


def test_connector_release_examples_are_valid_and_safe() -> None:
    for relative in EXAMPLES:
        payload = _json(relative)
        if relative.startswith("examples/"):
            assert payload["synthetic"] is True
        _assert_false_keys(payload)

    decision = _json("examples/connectors/connector-implementation-readiness-decision.json")
    assert decision["implementation_approved"] is False
    assert decision["future_adr_required"] is True


def test_connector_release_scripts_are_executable_and_pass() -> None:
    scripts = [
        (
            "scripts/connector-release-no-go-regression.sh",
            "Connector release no-go regression PASS",
        ),
        ("scripts/connector-release-gate.sh", "Connector release gate PASS"),
        ("scripts/connector-safety-freeze.sh", "Connector safety freeze PASS"),
    ]
    env = os.environ.copy()
    env["AION_CONNECTOR_SAFETY_FREEZE_SKIP_FULL_CHECK"] = "1"

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


def test_connector_release_gate_keeps_blocked_files_absent() -> None:
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
