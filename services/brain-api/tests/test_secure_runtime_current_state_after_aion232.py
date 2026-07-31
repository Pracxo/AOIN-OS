from secure_runtime_aion232_test_helpers import AION232, PASS_DECISION, program


def test_current_state_after_aion232_points_to_aion233_and_keeps_runtime_disabled() -> None:
    state = program()
    assert (
        state["program_state"]
        == "controlled_model_gateway_implemented_reference_simulation_only_pending_closeout"
    )
    assert state["secure_runtime_foundation_operator_evaluation_passed"] is True
    assert state["secure_runtime_foundation_operator_evaluation_id"] == "AION-SRIPE-001"
    assert state["secure_runtime_foundation_operator_evaluation_decision"] == PASS_DECISION
    assert state["active_sri_implementation_authorization_count"] == 1
    assert state["active_sri_implementation_authorization"] == AION232
    assert state["active_sri_implementation_task"] == "AION-233"
    assert state["formal_closeout_task"] == "AION-234"
    assert state["model_gateway_implemented"] is True
    assert state["model_gateway_state"] == (
        "implemented_provider_neutral_reference_simulation_only_pending_AION-234_closeout"
    )
    assert state["production_runtime_authorized"] is False
    assert state["actual_model_provider_call_enabled"] is False
    assert state["provider_network_egress_enabled"] is False
    assert state["connector_execution_enabled"] is False
    assert state["actual_tool_execution_enabled"] is False
    assert state["v02_release_ready"] is False
