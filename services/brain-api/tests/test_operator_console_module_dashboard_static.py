"""AION-090 static module lifecycle dashboard regression tests."""

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

NEW_DEMO_FILES = [
    "module-lifecycle-dashboard.json",
    "generic-knowledge-trail.json",
    "module-activation-blockers.json",
    "module-mock-runtime-trail.json",
    "module-review-checklist.json",
]


def test_module_dashboard_demo_json_files_exist_and_are_valid() -> None:
    for name in NEW_DEMO_FILES:
        payload = _json(DEMO_DIR / name)
        assert payload["read_only"] is True
        assert payload["redaction_applied"] is True
        assert payload["status"]
        assert isinstance(payload["sections"], list)


def test_lifecycle_dashboard_stages_and_safety_labels() -> None:
    dashboard = _json(DEMO_DIR / "module-lifecycle-dashboard.json")
    assert dashboard["module_key"] == "generic.knowledge_intelligence"
    assert dashboard["module_name"] == "Generic Knowledge Intelligence"
    labels = dashboard["safety_labels"]
    assert labels["activation_allowed"] is False
    assert labels["execution_allowed"] is False
    assert labels["registration_allowed"] is False
    assert labels["code_loaded"] is False
    assert labels["external_calls_made"] is False
    stages = {stage["stage_key"] for stage in dashboard["stages"]}
    assert "activation_gate" in stages
    assert "module_mock_runtime" in stages


def test_generic_knowledge_trail_lists_five_inactive_capabilities() -> None:
    trail = _json(DEMO_DIR / "generic-knowledge-trail.json")
    capabilities = trail["capabilities"]
    assert {item["capability_key"] for item in capabilities} == {
        "generic.knowledge.retrieve",
        "generic.knowledge.summarize",
        "generic.knowledge.ground",
        "generic.knowledge.explain",
        "generic.knowledge.answer",
    }
    for item in capabilities:
        assert item["controlled_supported"] is False
        assert item["dry_run_supported"] is True
        assert item["activation_allowed"] is False
        assert item["external_calls_made"] is False
        assert item["code_loaded"] is False


def test_activation_blockers_are_expected_and_not_bypassable() -> None:
    blockers = _json(DEMO_DIR / "module-activation-blockers.json")
    blocker_keys = {item["blocker_key"] for item in blockers["blockers"]}
    assert "activation_disabled" in blocker_keys
    assert "code_loading_disabled" in blocker_keys
    assert "package_install_disabled" in blocker_keys
    assert "dynamic_route_registration_disabled" in blocker_keys
    assert "runtime_registration_disabled" in blocker_keys
    assert all(item["bypassable"] is False for item in blockers["blockers"])


def test_mock_runtime_trail_is_synthetic_only() -> None:
    mock = _json(DEMO_DIR / "module-mock-runtime-trail.json")
    assert mock["synthetic"] is True
    assert mock["external_calls_made"] is False
    assert mock["code_loaded"] is False
    assert mock["activation_allowed"] is False
    assert mock["execution_allowed"] is False
    assert "confidence" in mock
    assert all(run["synthetic"] is True for run in mock["mock_runs"])


def test_review_checklist_is_review_only() -> None:
    review = _json(DEMO_DIR / "module-review-checklist.json")
    assert review["approval_scope"] == "review_only"
    checks = {item["check_key"] for item in review["checklist"]}
    assert "manifest_valid" in checks
    assert "no_executable_payload" in checks
    assert "activation_blocked" in checks
    assert "mock_runtime_synthetic" in checks


def test_static_markup_and_script_boundaries() -> None:
    html = _text(STATIC_DIR / "index.html")
    app = _text(STATIC_DIR / "app.js")
    css = _text(STATIC_DIR / "styles.css").lower()
    assert "Module Lifecycle" in html
    assert "This dashboard is read-only. Activation is blocked by design." in html
    assert "Generic Knowledge Intelligence Trail" in html
    assert 'method: "POST"' in app
    assert 'method: "PUT"' not in app
    assert 'method: "PATCH"' not in app
    assert 'method: "DELETE"' not in app
    assert "isLocalApiOrigin" in app
    assert 'parsed.hostname === "localhost"' in app
    assert 'parsed.hostname === "127.0.0.1"' in app
    assert "raw_prompt" in app
    assert "hidden_reasoning" in app
    assert "@import" not in css
    assert "url(http" not in css


def test_module_dashboard_docs_adr_and_script_exist() -> None:
    for relative in [
        "docs/operator-console/module-lifecycle-dashboard.md",
        "docs/operator-console/generic-knowledge-trail-view.md",
        "docs/operator-console/module-review-panel.md",
        "docs/operator-console/module-dashboard-safety-review.md",
        "docs/adr/0081-read-only-module-lifecycle-dashboard.md",
    ]:
        assert (ROOT / relative).exists(), relative
    assert "0081-read-only-module-lifecycle-dashboard.md" in _text(ROOT / "docs/adr/README.md")
    script = ROOT / "scripts/module-lifecycle-dashboard-check.sh"
    assert script.exists()
    assert os.access(script, os.X_OK)
    assert script.stat().st_mode & stat.S_IXUSR


def test_module_dashboard_script_and_static_scripts_pass() -> None:
    for command in [
        [str(ROOT / "scripts/module-lifecycle-dashboard-check.sh")],
        [str(ROOT / "scripts/operator-console-static-check.sh")],
        [str(ROOT / "scripts/operator-console-static-demo.sh"), "--offline-ok", "--skip-api"],
    ]:
        result = subprocess.run(
            command,
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        assert "PASS" in result.stdout


def test_no_runtime_or_package_files_changed() -> None:
    changed = _changed_files()
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
