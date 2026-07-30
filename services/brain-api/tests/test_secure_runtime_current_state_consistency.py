from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_current_state_marks_aion231_implemented_pending_aion232() -> None:
    program = json.loads(
        (REPO_ROOT / "docs/secure-runtime-integration/program-ledger.json").read_text()
    )
    status = (REPO_ROOT / "docs/project-status.md").read_text()

    assert program["program_state"] == (
        "secure_runtime_foundation_implemented_local_operator_simulation_only_pending_closeout"
    )
    assert program["secure_runtime_foundation_implemented"] is True
    assert program["secure_runtime_implemented"] is True
    assert program["active_sri_implementation_authorization"] == "AION-230-SRI-0001"
    assert program["formal_closeout_task"] == "AION-232"
    assert "AION-232" in status
    assert "v0.2 remains unreleased" in status
