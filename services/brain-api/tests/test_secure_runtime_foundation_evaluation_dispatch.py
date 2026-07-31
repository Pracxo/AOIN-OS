from secure_runtime_aion232_test_helpers import scenario


def test_dispatch_is_simulation_only_with_no_provider_connector_or_tool_effect() -> None:
    reqs = scenario("simulation_only_dispatch")["requirements"]
    assert reqs["one_deterministic_simulated_dispatch"] is True
    assert reqs["fixed_input_produces_fixed_result"] is True
    for key in (
        "no_real_brain_invocation",
        "no_model_call",
        "no_connector_call",
        "no_tool_execution",
        "no_shell",
        "no_subprocess",
        "no_browser",
        "no_module",
        "no_production_write",
        "no_hidden_reasoning_retained",
        "all_effect_flags_false",
    ):
        assert reqs[key] is True
