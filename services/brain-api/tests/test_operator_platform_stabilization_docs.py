"""AION-102 operator platform stabilization regression tests."""

from __future__ import annotations

import json
import os
import stat
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
EXAMPLE_DIR = ROOT / "examples" / "operator-console"
AION108_ALLOWED_CHANGED_FILES = {
    "services/brain-api/src/aion_brain/api/connector_runtime.py",
    "services/brain-api/src/aion_brain/api/connector_simulator.py",
    "services/brain-api/src/aion_brain/api/connector_policy.py",
    "services/brain-api/src/aion_brain/api/connector_sandbox.py",
    "services/brain-api/src/aion_brain/api/connector_credentials.py",
}


def test_operator_platform_stabilization_docs_and_adr_exist() -> None:
    for relative in [
        "docs/operator-console/operator-platform-regression-matrix.md",
        "docs/operator-console/operator-platform-freeze-gate.md",
        "docs/operator-console/operator-platform-long-running-checks.md",
        "docs/operator-console/operator-platform-stabilization-runbook.md",
        "docs/operator-console/operator-platform-regression-evidence.md",
        "docs/adr/0093-operator-platform-stabilization-gate.md",
    ]:
        assert (ROOT / relative).exists(), relative

    matrix_doc = _text(ROOT / "docs/operator-console/operator-platform-regression-matrix.md")
    for required in [
        "## Purpose",
        "Regression area",
        "Expected result",
        "Release blocker conditions",
        "Frequency",
        "Owner role",
        "Evidence output",
    ]:
        assert required in matrix_doc
    assert "0093-operator-platform-stabilization-gate.md" in _text(ROOT / "docs/adr/README.md")


def test_operator_platform_regression_examples_are_valid() -> None:
    matrix = _json(EXAMPLE_DIR / "operator-platform-regression-matrix.json")
    areas = {row["area"] for row in matrix["areas"]}
    for required in [
        "static console safety",
        "UI release gate",
        "module lifecycle dashboard",
        "provider hardening dashboard",
        "operator actions",
        "action authorization",
        "local auth",
        "local session",
        "role filtering",
        "production auth architecture",
        "disabled auth runtime",
        "docs audit",
        "boundary check",
        "repository health",
    ]:
        assert required in areas
    assert all(row["expected_status"] == "passed" for row in matrix["areas"])
    assert all(row["release_blocker"] is True for row in matrix["areas"])
    assert all(row["script"].startswith("./scripts/") for row in matrix["areas"])

    freeze = _json(EXAMPLE_DIR / "operator-platform-freeze-gate-result.json")
    assert freeze["status"] == "passed"
    flags = freeze["safety_flags"]
    assert flags["static_console_read_only"] is True
    for key in [
        "auth_runtime_enabled",
        "production_auth_enabled",
        "write_controls_present",
        "activation_controls_present",
        "execution_controls_present",
        "provider_call_controls_present",
        "external_calls_enabled",
        "frontend_dependencies_present",
        "package_install_allowed",
    ]:
        assert flags[key] is False

    evidence = _json(EXAMPLE_DIR / "operator-platform-regression-evidence.json")
    assert evidence["status"] == "passed"
    assert all(row["expected_status"] == "passed" for row in evidence["evidence"])
    assert all(row["script"].startswith("./scripts/") for row in evidence["evidence"])


def test_operator_platform_stabilization_scripts_are_executable_and_composed() -> None:
    scripts = [
        ROOT / "scripts/operator-platform-regression.sh",
        ROOT / "scripts/operator-platform-freeze-gate.sh",
    ]
    for script in scripts:
        assert script.exists(), script
        assert os.access(script, os.X_OK)
        assert script.stat().st_mode & stat.S_IXUSR

    regression = _text(ROOT / "scripts/operator-platform-regression.sh")
    for command in [
        "./scripts/operator-platform-checkpoint.sh",
        "./scripts/ui-release-gate.sh",
        "./scripts/static-console-safety-check.sh",
        "./scripts/operator-console-static-check.sh",
        "./scripts/module-lifecycle-dashboard-check.sh",
        "./scripts/provider-dashboard-check.sh",
        "./scripts/operator-actions-check.sh",
        "./scripts/action-authorization-check.sh",
        "./scripts/auth-runtime-check.sh",
        "./scripts/production-auth-architecture-check.sh",
        "./scripts/local-auth-check.sh",
        "./scripts/local-session-check.sh",
        "./scripts/role-filter-check.sh",
        "./scripts/docs-check.sh",
        "./scripts/final-docs-audit.sh",
        "./scripts/verify-no-domain-drift.sh",
        "./scripts/boundary-check.sh",
        "./scripts/check.sh",
    ]:
        assert command in regression

    freeze_gate = _text(ROOT / "scripts/operator-platform-freeze-gate.sh")
    assert "./scripts/operator-platform-regression.sh" in freeze_gate
    assert "git diff --check" in freeze_gate
    assert "aion-v0.1.0" in freeze_gate


def test_operator_platform_stabilization_keeps_blocked_files_absent() -> None:
    changed = _changed_files() - AION108_ALLOWED_CHANGED_FILES
    blocked_names = {
        "package.json",
        "package-lock.json",
        "pnpm-lock.yaml",
        "yarn.lock",
        "bun.lockb",
    }
    blocked_prefixes = (
        "vite.config.",
        "next.config.",
        "tailwind.config.",
        "webpack.config.",
    )
    assert not any(Path(name).name in blocked_names for name in changed)
    assert not any(Path(name).name.startswith(blocked_prefixes) for name in changed)
    assert not any("migrations" in Path(name).parts for name in changed)
    assert not any(name.startswith("services/brain-api/src/aion_brain/api/") for name in changed)
    assert not any("/routers/" in name or name.endswith("_router.py") for name in changed)


def test_operator_platform_stabilization_docs_keep_no_go_boundaries() -> None:
    combined = "\n".join(
        _text(ROOT / relative).lower()
        for relative in [
            "docs/operator-console/operator-platform-regression-matrix.md",
            "docs/operator-console/operator-platform-freeze-gate.md",
            "docs/operator-console/operator-platform-long-running-checks.md",
            "docs/operator-console/operator-platform-stabilization-runbook.md",
            "docs/operator-console/operator-platform-regression-evidence.md",
            "docs/adr/0093-operator-platform-stabilization-gate.md",
        ]
    )
    for required in [
        "frontend dependency",
        "production auth",
        "write",
        "activation",
        "execution",
        "provider",
        "external call",
        "no runtime subsystem",
        "no package installation",
    ]:
        assert required in combined
    assert "production ready" not in combined
    assert "production-ready" not in combined
    assert "ready for production" not in combined


def _json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def _text(path: Path) -> str:
    return path.read_text()


def _changed_files() -> set[str]:
    files: set[str] = set()
    for command in [
        ("diff", "--name-only", "--diff-filter=ACMRT", "HEAD", "--"),
        ("diff", "--cached", "--name-only", "--diff-filter=ACMRT", "--"),
        ("ls-files", "--others", "--exclude-standard"),
    ]:
        result = subprocess.run(
            ["git", *command],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        files.update(line.strip() for line in result.stdout.splitlines() if line.strip())

    for ref in ("origin/main", "main"):
        merge_base = subprocess.run(
            ["git", "merge-base", "HEAD", ref],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        if merge_base.returncode == 0 and merge_base.stdout.strip():
            result = subprocess.run(
                [
                    "git",
                    "diff",
                    "--name-only",
                    "--diff-filter=ACMRT",
                    f"{merge_base.stdout.strip()}..HEAD",
                    "--",
                ],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            files.update(line.strip() for line in result.stdout.splitlines() if line.strip())
            break

    return files
