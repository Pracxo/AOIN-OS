from __future__ import annotations

from secure_runtime_aion232_test_helpers import REPO_ROOT, program


def test_current_state_marks_aion235_implemented_pending_closeout() -> None:
    state = program()
    status = (REPO_ROOT / "docs/project-status.md").read_text()
    assert state["program_state"] in {
        "sandboxed_capability_runtime_implemented_reference_only_pending_closeout",
        "capability_runtime_evaluated_operator_console_integration_authorized_not_implemented",
    }
    assert state["secure_runtime_foundation_implemented"] is True
    assert state["secure_runtime_implemented"] is True
    active_state = (
        state["active_sri_implementation_authorization"],
        state["active_sri_implementation_task"],
        state["formal_closeout_task"],
    )
    assert active_state in {
        ("AION-234-SRI-0003", "AION-235", "AION-236"),
        ("AION-236-SRI-0004", "AION-237", "AION-238"),
    }
    assert state["model_gateway_implemented"] is True
    assert state["sandboxed_capability_runtime_implemented"] is True
    assert "AION-232" in status
    assert "AION-233" in status
    assert "AION-234-SRI-0003" in status
    assert "v0.2 remains unreleased" in status
