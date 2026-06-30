"""AION-101 operator platform checkpoint regression tests."""

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


def test_operator_platform_checkpoint_docs_and_adr_exist() -> None:
    for relative in [
        "docs/operator-console/operator-platform-phase-checkpoint.md",
        "docs/operator-console/operator-platform-evidence-pack.md",
        "docs/operator-console/operator-platform-risk-register.md",
        "docs/operator-console/operator-platform-next-phase.md",
        "docs/operator-console/operator-platform-release-readiness.md",
        "docs/operator-console/operator-platform-checkpoint.md",
        "docs/adr/0092-operator-platform-checkpoint.md",
    ]:
        assert (ROOT / relative).exists(), relative

    checkpoint_doc = _text(ROOT / "docs/operator-console/operator-platform-phase-checkpoint.md")
    for heading in [
        "## Purpose",
        "## Phase scope",
        "## Completed AION tasks from AION-089 to AION-100",
        "## What is safe today",
        "## What remains blocked",
        "## Evidence commands",
        "## Merge requirements",
        "## No-go conditions",
        "## Next recommended phase",
    ]:
        assert heading in checkpoint_doc
    assert "0092-operator-platform-checkpoint.md" in _text(ROOT / "docs/adr/README.md")


def test_operator_platform_examples_are_valid_and_complete() -> None:
    checkpoint = _json(EXAMPLE_DIR / "operator-platform-checkpoint.json")
    assert checkpoint["status"] == "passed"
    assert checkpoint["read_only"] is True
    assert checkpoint["local_only"] is True
    assert checkpoint["production_auth_enabled"] is False
    assert checkpoint["external_calls_enabled"] is False
    assert checkpoint["activation_enabled"] is False
    assert checkpoint["execution_enabled"] is False
    assert checkpoint["frontend_dependencies_present"] is False
    assert checkpoint["build_system_present"] is False
    assert set(checkpoint["covered_tasks"]) == {f"AION-{number:03d}" for number in range(89, 101)}

    evidence = _json(EXAMPLE_DIR / "operator-platform-evidence-pack.json")
    areas = {item["area"] for item in evidence["evidence"]}
    for required in [
        "Static console safety",
        "Module lifecycle dashboard",
        "Provider dashboard",
        "Operator actions",
        "Local auth",
        "Local session",
        "Role filtering",
        "Action authorization",
        "Production auth architecture",
        "Disabled auth prototype",
        "UI release gate",
        "Docs audit",
        "Boundary check",
        "Repository health",
    ]:
        assert required in areas
    assert all(item["expected_status"] == "passed" for item in evidence["evidence"])
    assert all(item["script"].startswith("./scripts/") for item in evidence["evidence"])

    risk_register = _json(EXAMPLE_DIR / "operator-platform-risk-register.json")
    risks = {item["risk"] for item in risk_register["risks"]}
    for required in [
        "frontend dependency creep",
        "hidden write action",
        "activation leakage",
        "auth runtime enablement",
        "credential/session storage",
        "raw prompt exposure",
        "hidden reasoning exposure",
        "provider call leakage",
        "external URL call",
        "stale demo data",
        "policy bypass",
        "audit bypass",
    ]:
        assert required in risks
    assert all(item["control"] for item in risk_register["risks"])
    assert all(item["no_go_condition"] for item in risk_register["risks"])


def test_operator_platform_checkpoint_script_exists_and_passes() -> None:
    script = ROOT / "scripts/operator-platform-checkpoint.sh"
    assert script.exists()
    assert os.access(script, os.X_OK)
    assert script.stat().st_mode & stat.S_IXUSR

    result = subprocess.run(
        [str(script)],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert "Operator platform checkpoint PASS" in result.stdout


def test_operator_platform_checkpoint_keeps_blocked_files_absent() -> None:
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
    changed = _changed_files() - AION108_ALLOWED_CHANGED_FILES
    assert not any(Path(name).name in blocked_names for name in changed)
    assert not any(Path(name).name.startswith(blocked_prefixes) for name in changed)
    assert not any("migrations" in Path(name).parts for name in changed)
    assert not any(name.startswith("services/brain-api/src/aion_brain/api/") for name in changed)
    assert not any("/routers/" in name or name.endswith("_router.py") for name in changed)


def test_operator_platform_checkpoint_docs_keep_no_go_boundaries() -> None:
    combined = "\n".join(
        _text(ROOT / relative).lower()
        for relative in [
            "docs/operator-console/operator-platform-phase-checkpoint.md",
            "docs/operator-console/operator-platform-evidence-pack.md",
            "docs/operator-console/operator-platform-risk-register.md",
            "docs/operator-console/operator-platform-next-phase.md",
            "docs/operator-console/operator-platform-release-readiness.md",
            "docs/adr/0092-operator-platform-checkpoint.md",
        ]
    )
    for required in [
        "production auth",
        "login/logout",
        "frontend dependency",
        "write",
        "activation",
        "execution",
        "provider",
        "external call",
        "not production ui",
    ]:
        assert required in combined
    assert "production ready" not in combined
    assert "production-ready" not in combined
    assert "ready for production" not in combined


def _json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def _text(path: Path) -> str:
    return path.read_text()


def _git_lines(*args: str) -> list[str]:
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return [line for line in result.stdout.splitlines() if line]


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


def _merge_base(ref: str) -> str | None:
    result = subprocess.run(
        ["git", "merge-base", "HEAD", ref],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return None
    return result.stdout.strip() or None


def _comparison_base() -> str | None:
    candidates = ["origin/main", "main"]
    github_base_ref = os.environ.get("GITHUB_BASE_REF")
    if github_base_ref:
        candidates.extend([f"origin/{github_base_ref}", github_base_ref])

    for candidate in candidates:
        if _git_ref_exists(candidate):
            merge_base = _merge_base(candidate)
            if merge_base:
                return merge_base

    if _git_ref_exists("HEAD~1"):
        return _merge_base("HEAD~1") or "HEAD~1"

    return None


def _changed_files() -> set[str]:
    changed = set(_git_lines("diff", "--name-only", "--diff-filter=ACMRT", "HEAD", "--"))
    changed.update(_git_lines("diff", "--cached", "--name-only", "--diff-filter=ACMRT", "--"))
    changed.update(_git_lines("ls-files", "--others", "--exclude-standard"))
    merge_base = _comparison_base()
    if merge_base is not None:
        changed.update(
            _git_lines("diff", "--name-only", "--diff-filter=ACMRT", f"{merge_base}..HEAD", "--")
        )
    return changed
