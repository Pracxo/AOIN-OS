from __future__ import annotations

import json
import os
import stat
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
STATIC_DIR = ROOT / "operator-console-static"
DEMO_DIR = STATIC_DIR / "demo-data"


def test_operator_actions_static_panel_and_demo_json_are_safe() -> None:
    html = (STATIC_DIR / "index.html").read_text()
    app = (STATIC_DIR / "app.js").read_text()
    assert "Operator Actions" in html
    assert "operator_actions" in app
    assert 'method: "PUT"' not in app
    assert 'method: "PATCH"' not in app
    assert 'method: "DELETE"' not in app

    preview = json.loads((DEMO_DIR / "operator-action-preview.json").read_text())
    assert preview["execution_allowed"] is False
    assert preview["external_calls_allowed"] is False
    assert preview["activation_allowed"] is False
    assert preview["would_execute"] is False


def test_operator_actions_check_script_passes() -> None:
    script = ROOT / "scripts/operator-actions-check.sh"
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
    assert "Operator actions check PASS" in result.stdout
