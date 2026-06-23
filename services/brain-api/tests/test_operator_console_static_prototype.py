"""AION-089 static Operator Console prototype regression tests."""

from __future__ import annotations

import json
import os
import stat
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
STATIC_DIR = ROOT / "operator-console-static"
DEMO_DIR = STATIC_DIR / "demo-data"

DEMO_FILES = [
    "overview-view-model.json",
    "module-lifecycle-view-model.json",
    "provider-hardening-view-model.json",
    "release-readiness-view-model.json",
    "incidents-view-model.json",
    "settings-safety-view-model.json",
]

REQUIRED_ACTIONS = {
    "activate_module",
    "activate_capability",
    "load_code",
    "execute_tool",
    "enable_external_model_calls",
    "hard_delete",
}


def test_static_console_files_exist() -> None:
    for relative in [
        "README.md",
        "index.html",
        "styles.css",
        "app.js",
    ]:
        assert (STATIC_DIR / relative).exists(), relative
    for name in DEMO_FILES:
        assert (DEMO_DIR / name).exists(), name


def test_static_console_demo_json_is_valid_and_safe() -> None:
    for name in DEMO_FILES:
        payload = _json(DEMO_DIR / name)
        assert payload["read_only"] is True
        assert payload["redaction_applied"] is True
        assert payload["status"]
        assert isinstance(payload["sections"], list)
        actions = {item["action_key"] for item in payload["forbidden_actions"]}
        assert actions == REQUIRED_ACTIONS
        serialized = json.dumps(payload, sort_keys=True).lower()
        for forbidden in [
            "raw_prompt",
            "hidden_reasoning",
            "chain_of_thought",
            "password",
            "api_key",
            "private_key",
            "authorization",
            "bearer ",
            "sk-",
            "ghp_",
        ]:
            assert forbidden not in serialized


def test_static_console_banner_and_descriptors_are_present() -> None:
    html = _text(STATIC_DIR / "index.html")
    assert "AION Operator Console Prototype — local, read-only, no activation" in html
    assert "Forbidden Action Descriptors" in html
    assert "read-only prototype" in html
    assert "no external calls" in html


def test_app_blocks_non_localhost_and_uses_redaction() -> None:
    app = _text(STATIC_DIR / "app.js")
    assert 'DEFAULT_API_BASE = "http://localhost:8080"' in app
    assert "isLocalApiOrigin" in app
    assert 'parsed.hostname === "localhost"' in app
    assert 'parsed.hostname === "127.0.0.1"' in app
    assert "apiAllowed: false" in app
    assert "/brain/operator-console/view-model" in app
    for key in [
        "raw_prompt",
        "hidden_reasoning",
        "chain_of_thought",
        "password",
        "token",
        "api_key",
        "secret",
        "private_key",
        "credential",
        "authorization",
        "bearer",
    ]:
        assert key in app


def test_app_has_no_write_methods_or_external_fetch_targets() -> None:
    app = _text(STATIC_DIR / "app.js")
    assert 'method: "POST"' in app
    assert 'method: "PUT"' not in app
    assert 'method: "PATCH"' not in app
    assert 'method: "DELETE"' not in app
    assert "localStorage" not in app
    assert "import(" not in app
    assert "require(" not in app
    external_urls = [
        line
        for line in app.splitlines()
        if "http://" in line or "https://" in line
        if "localhost" not in line and "127.0.0.1" not in line
    ]
    assert external_urls == []


def test_css_has_no_external_imports() -> None:
    css = _text(STATIC_DIR / "styles.css").lower()
    assert "@import" not in css
    assert "url(http" not in css


def test_static_console_docs_and_adr_exist() -> None:
    for relative in [
        "docs/operator-console/static-console-prototype.md",
        "docs/operator-console/static-console-runbook.md",
        "docs/operator-console/static-console-safety-review.md",
        "docs/operator-console/static-console-test-plan.md",
        "docs/adr/0080-static-local-operator-console-prototype.md",
    ]:
        assert (ROOT / relative).exists(), relative
    assert "0080-static-local-operator-console-prototype.md" in _text(ROOT / "docs/adr/README.md")


def test_no_frontend_dependency_or_build_files_added() -> None:
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


def test_static_console_scripts_exist_and_pass() -> None:
    check_script = ROOT / "scripts/operator-console-static-check.sh"
    demo_script = ROOT / "scripts/operator-console-static-demo.sh"
    for script in [check_script, demo_script]:
        assert script.exists()
        assert os.access(script, os.X_OK)
        assert script.stat().st_mode & stat.S_IXUSR

    check = subprocess.run(
        [str(check_script)],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert "Operator console static check PASS" in check.stdout

    demo = subprocess.run(
        [str(demo_script), "--offline-ok", "--skip-api"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert "Operator console static demo PASS" in demo.stdout


def _json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def _text(path: Path) -> str:
    return path.read_text()


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
