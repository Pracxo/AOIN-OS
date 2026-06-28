from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def test_static_console_action_authorization_panel_exists() -> None:
    index = (ROOT / "operator-console-static/index.html").read_text()
    app = (ROOT / "operator-console-static/app.js").read_text()
    preview = json.loads(
        (
            ROOT / "operator-console-static/demo-data/action-authorization-preview.json"
        ).read_text()
    )
    deny_matrix = json.loads(
        (
            ROOT / "operator-console-static/demo-data/action-authorization-deny-matrix.json"
        ).read_text()
    )

    assert "action-authorization-panel" in index
    assert "ACTION_AUTHORIZATION_DEMOS" in app
    assert preview["dry_run_only"] is True
    assert preview["write_allowed"] is False
    assert preview["execution_allowed"] is False
    assert preview["activation_allowed"] is False
    assert preview["external_calls_allowed"] is False
    assert deny_matrix["denials"]
