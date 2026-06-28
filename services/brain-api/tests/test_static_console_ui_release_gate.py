"""AION-100 static console UI release gate regression tests."""

from __future__ import annotations

import json
import os
import re
import stat
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
STATIC_DIR = ROOT / "operator-console-static"
EXAMPLE_DIR = ROOT / "examples" / "operator-console"

EXAMPLE_FILES = [
    "static-console-artifact-manifest.json",
    "ui-release-gate-result.json",
    "ui-safety-matrix.json",
]


def test_ui_release_gate_scripts_exist_and_pass() -> None:
    for relative in [
        "scripts/static-console-safety-check.sh",
        "scripts/ui-release-gate.sh",
    ]:
        script = ROOT / relative
        assert script.exists(), relative
        assert os.access(script, os.X_OK)
        assert script.stat().st_mode & stat.S_IXUSR

    for command, expected in [
        (
            [str(ROOT / "scripts/static-console-safety-check.sh")],
            "Static console safety check PASS",
        ),
        ([str(ROOT / "scripts/ui-release-gate.sh")], "UI release gate PASS"),
    ]:
        result = subprocess.run(
            command,
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        assert expected in result.stdout


def test_ui_release_gate_examples_are_valid_and_safe() -> None:
    for name in EXAMPLE_FILES:
        payload = _json(EXAMPLE_DIR / name)
        serialized = json.dumps(payload, sort_keys=True).lower()
        assert "raw_prompt" not in serialized
        assert "hidden_reasoning" not in serialized
        assert "chain_of_thought" not in serialized
        assert "password" not in serialized
        assert "private_key" not in serialized
        assert "bearer " not in serialized
        assert "sk-" not in serialized
        assert "ghp_" not in serialized


def test_ui_release_gate_result_and_matrix_shape() -> None:
    result = _json(EXAMPLE_DIR / "ui-release-gate-result.json")
    assert result["status"] == "passed"
    assert result["safety_flags"]["no_frontend_dependencies"] is True
    assert result["safety_flags"]["no_write_verbs"] is True
    assert result["safety_flags"]["production_auth_enabled"] is False
    assert result["safety_flags"]["auth_runtime_enabled"] is False
    assert result["safety_flags"]["execution_allowed"] is False
    assert result["safety_flags"]["activation_allowed"] is False
    assert result["safety_flags"]["external_calls_allowed"] is False

    matrix = _json(EXAMPLE_DIR / "ui-safety-matrix.json")
    controls = {row["control"] for row in matrix["controls"]}
    for required in [
        "no frontend dependencies",
        "no build step",
        "no external scripts",
        "localhost-only API",
        "read-only view models",
        "no write verbs",
        "no activation controls",
        "no execution controls",
        "no provider call controls",
        "no login form",
        "no credential inputs",
        "no token/cookie/session persistence",
        "no raw prompt display",
        "no hidden reasoning display",
        "no secret display",
        "demo fallback",
    ]:
        assert required in controls
    assert all(row["checked_by_script"] is True for row in matrix["controls"])
    assert all(row["release_blocker_if_failed"] is True for row in matrix["controls"])


def test_static_console_release_gate_banners_and_controls() -> None:
    html = _text(STATIC_DIR / "index.html")
    lowered = html.lower()
    for banner in [
        "ui release gate: read-only, local, dependency-free",
        "read-only",
        "no activation",
        "no execution",
        "no provider calls",
        "no login",
        "no credentials",
    ]:
        assert banner in lowered
    assert "<form" not in lowered
    assert "<input" not in lowered
    assert 'type="password"' not in lowered
    assert "name=\"token\"" not in lowered
    assert "name=\"cookie\"" not in lowered
    assert "name=\"credential\"" not in lowered

    for attrs, text in _buttons(html):
        normalized = text.lower()
        dangerous = any(
            word in normalized
            for word in [
                "activate",
                "execute",
                "provider call",
                "call provider",
                "login",
                "credential",
            ]
        )
        if dangerous:
            assert "disabled" in attrs.lower()
            assert normalized.startswith(("no ", "actions disabled", "preview only", "demo only"))


def test_static_console_app_and_css_keep_safety_boundaries() -> None:
    app = _text(STATIC_DIR / "app.js")
    css = _text(STATIC_DIR / "styles.css").lower()
    assert "isLocalApiOrigin" in app
    assert 'parsed.hostname === "localhost"' in app
    assert 'parsed.hostname === "127.0.0.1"' in app
    assert "apiAllowed: false" in app
    assert 'method: "PUT"' not in app
    assert 'method: "PATCH"' not in app
    assert 'method: "DELETE"' not in app
    assert "localStorage" not in app
    assert "sessionStorage" not in app
    assert "@import" not in css
    assert "url(http" not in css


def test_no_frontend_package_or_build_files_added() -> None:
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
    changed = _changed_files()
    assert not any(Path(name).name in blocked_names for name in changed)
    assert not any(Path(name).name.startswith(blocked_prefixes) for name in changed)


def test_ui_release_gate_docs_and_adr_exist() -> None:
    for relative in [
        "docs/operator-console/ui-release-gate.md",
        "docs/operator-console/static-console-safety-matrix.md",
        "docs/operator-console/operator-platform-checkpoint.md",
        "docs/operator-console/post-v0.1-ui-no-go-conditions.md",
        "docs/operator-console/static-console-artifact-manifest.md",
        "docs/operator-console/ui-release-evidence-summary.md",
        "docs/adr/0091-static-console-ui-release-gate.md",
    ]:
        assert (ROOT / relative).exists(), relative
    assert "0091-static-console-ui-release-gate.md" in _text(ROOT / "docs/adr/README.md")


def _json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def _text(path: Path) -> str:
    return path.read_text()


def _buttons(html: str) -> list[tuple[str, str]]:
    pattern = re.compile(r"<button\b(?P<attrs>[^>]*)>(?P<body>.*?)</button>", re.I | re.S)
    buttons: list[tuple[str, str]] = []
    for match in pattern.finditer(html):
        text = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", match.group("body"))).strip()
        buttons.append((match.group("attrs"), text))
    return buttons


def _changed_files() -> list[str]:
    tracked = subprocess.run(
        ["git", "diff", "--name-only", "--diff-filter=ACMRT", "HEAD", "--"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    untracked = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return [*tracked.stdout.splitlines(), *untracked.stdout.splitlines()]
