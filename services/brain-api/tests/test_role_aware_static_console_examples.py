from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
STATIC_DIR = ROOT / "operator-console-static"
DEMO_DIR = STATIC_DIR / "demo-data"


def test_static_role_switcher_is_demo_only() -> None:
    html = (STATIC_DIR / "index.html").read_text()
    app = (STATIC_DIR / "app.js").read_text()

    assert "role-switcher" in html
    for role in ["viewer", "operator", "reviewer", "admin", "auditor"]:
        assert f'data-role="{role}"' in html
    assert 'data-role="system_service"' not in html
    assert "<form" not in html
    assert "localStorage" not in app
    assert "sessionStorage" not in app


def test_role_static_demo_files_are_safe() -> None:
    for name in [
        "role-viewer-dashboard.json",
        "role-operator-dashboard.json",
        "role-reviewer-dashboard.json",
        "role-auditor-dashboard.json",
        "role-admin-dashboard.json",
        "role-access-matrix.json",
    ]:
        payload = json.loads((DEMO_DIR / name).read_text())
        assert payload["read_only"] is True
        assert payload["redaction_applied"] is True
        assert payload["forbidden_actions_visible"] is True
        assert payload["write_allowed"] is False
        assert payload["execute_allowed"] is False
        assert payload["activation_allowed"] is False
        assert payload["external_calls_allowed"] is False


def test_role_filter_check_script_passes() -> None:
    script = ROOT / "scripts/role-filter-check.sh"
    assert os.access(script, os.X_OK)
    result = subprocess.run(
        [str(script)],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert "Role filter check PASS" in result.stdout
