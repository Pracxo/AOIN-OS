from __future__ import annotations

from secure_runtime_aion232_test_helpers import AION232, REPO_ROOT, program


def test_current_state_marks_aion231_evaluated_and_aion233_authorized() -> None:
    state = program()
    status = (REPO_ROOT / "docs/project-status.md").read_text()
    assert (
        state["program_state"]
        == "controlled_model_gateway_implemented_reference_simulation_only_pending_closeout"
    )
    assert state["secure_runtime_foundation_implemented"] is True
    assert state["secure_runtime_implemented"] is True
    assert state["active_sri_implementation_authorization"] == AION232
    assert state["active_sri_implementation_task"] == "AION-233"
    assert state["formal_closeout_task"] == "AION-234"
    assert state["model_gateway_implemented"] is True
    assert "AION-232" in status
    assert "AION-233" in status
    assert "v0.2 remains unreleased" in status
