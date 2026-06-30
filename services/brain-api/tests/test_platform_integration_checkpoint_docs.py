"""AION-117 platform integration checkpoint regression tests."""

from __future__ import annotations

import json
import os
import stat
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]

DOCS = [
    "docs/platform/post-v01-platform-integration-checkpoint.md",
    "docs/platform/cross-phase-evidence-pack.md",
    "docs/platform/operator-connector-boundary-matrix.md",
    "docs/platform/future-runtime-boundary-freeze.md",
    "docs/platform/platform-integration-risk-register.md",
    "docs/platform/implementation-approval-state-summary.md",
    "docs/platform/platform-integration-closeout-checklist.md",
    "docs/adr/0108-post-v01-platform-integration-checkpoint.md",
]

EXAMPLES = [
    "examples/platform/post-v01-platform-integration-checkpoint.json",
    "examples/platform/cross-phase-evidence-pack.json",
    "examples/platform/operator-connector-boundary-matrix.json",
    "examples/platform/future-runtime-boundary-freeze.json",
    "examples/platform/implementation-approval-state-summary.json",
    "operator-console-static/demo-data/platform-integration-checkpoint.json",
    "operator-console-static/demo-data/future-runtime-boundary-freeze.json",
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
    "oauth_oidc_saml_runtime_approved",
    "code_loading_approved",
    "runtime_registration_approved",
    "capability_activation_approved",
    "package_files_added",
    "migrations_added",
    "api_runtime_execution_route_added",
    "sdk_resource_implementation_added",
    "cli_command_implementation_added",
    "frontend_dependencies_added",
    "aion_v0_1_0_touched",
}


def test_platform_integration_docs_exist_and_are_indexed() -> None:
    for relative in DOCS:
        assert (ROOT / relative).exists(), relative

    index = _text("docs/adr/README.md")
    assert "0108-post-v01-platform-integration-checkpoint.md" in index

    checkpoint = _text("docs/platform/post-v01-platform-integration-checkpoint.md")
    for heading in [
        "## Purpose",
        "## Scope",
        "## Operator platform summary",
        "## Connector platform summary",
        "## Current safe state",
        "## Disabled capabilities",
        "## Evidence scripts",
        "## Release blockers",
        "## Checkpoint decision",
        "## Next phase boundary",
    ]:
        assert heading in checkpoint

    approval = _text("docs/platform/implementation-approval-state-summary.md")
    for line in [
        "operator_write_execution_approved=false",
        "connector_implementation_approved=false",
        "production_auth_approved=false",
        "module_activation_approved=false",
        "external_calls_approved=false",
        "credential_storage_approved=false",
        "token_storage_approved=false",
        "sandbox_execution_approved=false",
    ]:
        assert line in approval

    adr = _text("docs/adr/0108-post-v01-platform-integration-checkpoint.md")
    assert "Decision: add a post-v0.1 platform integration checkpoint." in adr
    assert "Decision: keep all implementation approvals false." in adr
    assert "Constraint: no production auth implementation." in adr
    assert "Constraint: no connector runtime implementation." in adr
    assert "Constraint: no operator write execution." in adr
    assert "Constraint: no module activation." in adr
    assert "Constraint: no external calls." in adr
    assert "Constraint: no credential storage." in adr
    assert "Constraint: no token storage." in adr
    assert "Constraint: no sandbox execution." in adr


def test_platform_integration_examples_are_valid_and_safe() -> None:
    for relative in EXAMPLES:
        payload = _json(relative)
        if relative.startswith("examples/"):
            assert payload["synthetic"] is True
        assert payload["status"] == "passed"
        assert payload["checkpoint_passed"] is True
        assert payload["integration_gate_passed"] is True
        _assert_false_keys(payload)
        _assert_no_blocked_strings(payload)


def test_platform_integration_scripts_are_executable_and_wired() -> None:
    scripts = [
        ("scripts/platform-integration-checkpoint.sh", "platform integration checkpoint PASS"),
        ("scripts/platform-integration-freeze-check.sh", "platform integration freeze PASS"),
        (
            "scripts/platform-integration-no-go-regression.sh",
            "platform integration no-go regression PASS",
        ),
    ]
    for relative, expected in scripts:
        script = ROOT / relative
        assert script.exists(), relative
        assert os.access(script, os.X_OK)
        assert script.stat().st_mode & stat.S_IXUSR
        assert expected in script.read_text()

    checkpoint = _text("scripts/platform-integration-checkpoint.sh")
    for command in [
        "./scripts/operator-platform-regression.sh",
        "./scripts/operator-platform-freeze-gate.sh",
        "./scripts/connector-platform-regression.sh",
        "./scripts/connector-platform-stabilization-gate.sh",
        "./scripts/connector-platform-checkpoint.sh",
        "./scripts/connector-platform-freeze-check.sh",
        "./scripts/connector-release-gate.sh",
        "./scripts/connector-safety-freeze.sh",
        "./scripts/auth-prototype-review.sh",
        "./scripts/auth-no-go-regression.sh",
        "./scripts/module-activation-design-review.sh",
        "./scripts/module-activation-no-go-regression.sh",
        "./scripts/ui-release-gate.sh",
        "./scripts/static-console-safety-check.sh",
        "./scripts/docs-check.sh",
        "./scripts/final-docs-audit.sh",
        "./scripts/verify-no-domain-drift.sh",
        "./scripts/boundary-check.sh",
    ]:
        assert command in checkpoint

    freeze = _text("scripts/platform-integration-freeze-check.sh")
    assert "./scripts/check.sh" in freeze
    assert "PYTEST_CURRENT_TEST" in freeze
    assert "AION_AGGREGATE_GATE_RUNNING" in freeze
    assert "AION_CHECK_RUNNING" in freeze
    assert "PASS: full repository check deferred to outer gate" in freeze
    assert "aion-v0.1.0" in freeze

    no_go = _text("scripts/platform-integration-no-go-regression.sh")
    assert "source \"$ROOT_DIR/scripts/lib/portable-search.sh\"" in no_go
    assert "comparison_base()" in no_go
    assert "origin/main" in no_go
    assert "GITHUB_BASE_REF" in no_go
    assert "HEAD~1" in no_go


def test_platform_integration_static_console_is_wired() -> None:
    html = _text("operator-console-static/index.html")
    app = _text("operator-console-static/app.js")
    nav = _json("examples/operator-console/static-console-navigation-map.json")
    for command in [
        "./scripts/platform-integration-checkpoint.sh",
        "./scripts/platform-integration-freeze-check.sh",
        "./scripts/platform-integration-no-go-regression.sh",
    ]:
        assert command in html
        assert command in app
        assert command in nav["safe_copy_commands"]

    assert "platform-integration-checkpoint" in html
    assert "future-runtime-boundary-freeze" in html
    assert "loadPlatformIntegrationPanels" in app
    assert "renderPlatformIntegrationEvidence" in app


def test_platform_integration_keeps_blocked_files_absent() -> None:
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
    candidates.extend(["origin/main", "main"])
    if github_base_ref:
        candidates.extend([f"origin/{github_base_ref}", github_base_ref])

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
