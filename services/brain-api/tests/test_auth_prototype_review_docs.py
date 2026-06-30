"""AION-104 local auth prototype review gate regression tests."""

from __future__ import annotations

import json
import os
import stat
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
EXAMPLE_DIR = ROOT / "examples" / "auth"
AION108_ALLOWED_CHANGED_FILES = {
    "services/brain-api/src/aion_brain/api/connector_runtime.py",
    "services/brain-api/src/aion_brain/api/connector_simulator.py",
    "services/brain-api/src/aion_brain/api/connector_policy.py",
}


def test_auth_prototype_review_docs_and_adr_exist() -> None:
    for relative in [
        "docs/auth/local-auth-prototype-review.md",
        "docs/auth/auth-safety-evidence-pack.md",
        "docs/auth/auth-runtime-disabled-proof.md",
        "docs/auth/auth-traceability-matrix.md",
        "docs/auth/auth-no-go-regression-pack.md",
        "docs/auth/pre-implementation-auth-gate.md",
        "docs/adr/0095-local-auth-prototype-review-gate.md",
    ]:
        assert (ROOT / relative).exists(), relative

    index = _text(ROOT / "docs/adr/README.md")
    assert "0095-local-auth-prototype-review-gate.md" in index


def test_auth_review_examples_are_valid_and_safe() -> None:
    evidence = _json(EXAMPLE_DIR / "auth-safety-evidence-pack.json")
    assert evidence["status"] == "passed"
    areas = {row["area"] for row in evidence["evidence"]}
    for required in [
        "local auth design",
        "local auth contract",
        "dev identity simulation",
        "local session preview",
        "role filtering",
        "dry-run action authorization",
        "production auth architecture",
        "disabled auth runtime",
        "static console auth panels",
        "docs audit",
        "boundary checks",
    ]:
        assert required in areas
    assert all(row["expected_status"] == "passed" for row in evidence["evidence"])
    assert all(row["release_blocker"] is True for row in evidence["evidence"])

    proof = _json(EXAMPLE_DIR / "auth-runtime-disabled-proof.json")
    for key in [
        "production_auth_enabled",
        "auth_runtime_enabled",
        "credentials_enabled",
        "token_issuance_enabled",
        "cookie_issuance_enabled",
        "session_persistence_enabled",
        "login_endpoint_enabled",
        "logout_endpoint_enabled",
        "external_identity_provider_enabled",
        "provider_sdk_present",
        "package_files_present",
        "migration_present",
        "token_present",
        "cookie_present",
        "session_persisted",
        "protected_material_present",
        "write_allowed",
        "execute_allowed",
        "activation_allowed",
        "external_calls_allowed",
    ]:
        assert proof[key] is False

    trace = _json(EXAMPLE_DIR / "auth-traceability-matrix.json")
    surfaces = {row["surface"] for row in trace["rows"]}
    for required in [
        "role",
        "session",
        "action authorization",
        "policy",
        "static console",
        "audit",
        "forbidden action",
    ]:
        assert required in surfaces
    for row in trace["rows"]:
        assert row["write_allowed"] is False
        assert row["execute_allowed"] is False
        assert row["activation_allowed"] is False
        assert row["external_calls_allowed"] is False

    no_go = _json(EXAMPLE_DIR / "auth-no-go-regression-result.json")
    assert no_go["status"] == "passed"
    assert all(item["expected_status"] == "passed" for item in no_go["checks"])
    assert no_go["production_auth_enabled"] is False
    assert no_go["protected_material_present"] is False
    assert no_go["external_identity_provider_enabled"] is False


def test_auth_review_scripts_are_executable_and_pass() -> None:
    for relative, expected in [
        ("scripts/auth-no-go-regression.sh", "Auth no-go regression PASS"),
        ("scripts/auth-prototype-review.sh", "Auth prototype review PASS"),
    ]:
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
        )
        assert expected in result.stdout


def test_auth_review_keeps_blocked_files_absent() -> None:
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
    return files
