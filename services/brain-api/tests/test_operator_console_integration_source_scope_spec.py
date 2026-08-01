from __future__ import annotations

from operator_console_integration_test_support import REPO_ROOT, operator_auth


def test_operator_console_future_source_scope_recorded_but_absent():
    scope = operator_auth()["future_source_scope"]
    assert "services/brain-api/src/aion_brain/contracts/operator_console_integration.py" in scope
    assert not any((REPO_ROOT / item).exists() for item in scope)
    assert not (REPO_ROOT / "operator-console-static/live-console.js").exists()
