from secure_runtime_aion232_test_helpers import (
    MODEL_GATEWAY_SCOPE,
    active_authorization_record,
    program,
)


def test_model_gateway_scope_and_task_flow_are_recorded() -> None:
    record = active_authorization_record()
    state = program()
    assert record["authorization_scope"] == MODEL_GATEWAY_SCOPE
    assert state["current_task"] == (
        "AION-236 capability-runtime operator evaluation and operator-console integration "
        "authorization decision."
    )
    assert state["active_implementation_task"] == "AION-235"
    assert state["formal_closeout_task"] == "AION-236"
    assert state["model_gateway_authorized"] is True
    assert state["model_gateway_implemented"] is True
    assert state["sandboxed_capability_runtime_implemented"] is True
    assert state["secure_runtime_component_composition_for_model_gateway_authorized"] is True
    assert state["standalone_local_operator_runtime_pilot_authorized"] is False
