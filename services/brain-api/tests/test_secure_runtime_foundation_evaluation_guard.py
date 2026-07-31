from secure_runtime_aion232_test_helpers import scenario


def test_budget_kill_switch_and_runtime_guard_precedence_are_enforced() -> None:
    budget = scenario("side_effect_budget_enforcement")["requirements"]
    assert budget["every_prohibited_effect_counter_zero"] is True
    assert budget["selected_one_over_limit_fails_closed"] is True
    kill = scenario("operator_kill_switch")["requirements"]
    assert kill["active_kills_session"] is True
    assert kill["active_leaves_zero_active_requests"] is True
    guard = scenario("runtime_guard_precedence")["requirements"]
    assert guard["precedence_exact"] is True
    assert guard["allow_simulation_only_after_every_gate_passes"] is True
    assert guard["no_allow_execution_result"] is True
