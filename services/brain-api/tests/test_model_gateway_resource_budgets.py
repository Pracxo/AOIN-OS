from secure_runtime_aion232_test_helpers import authorization


def test_model_gateway_resource_limits_are_exact_and_zero_effect_limits_remain_zero() -> None:
    limits = authorization()["model_gateway_resource_limits"]
    assert limits["maximum_model_gateway_sessions"] == 1
    assert limits["maximum_requests_per_session"] == 100
    assert limits["maximum_concurrent_requests"] == 4
    assert limits["maximum_context_bytes_per_request"] == 4194304
    assert limits["maximum_input_tokens_per_request"] == 131072
    assert limits["maximum_output_tokens_per_request"] == 16384
    assert limits["maximum_retry_attempts_planned_per_request"] == 2
    assert limits["maximum_latency_budget_milliseconds"] == 120000
    for key, value in limits.items():
        if key.startswith("maximum_public_network") or key in {
            "maximum_model_provider_calls",
            "maximum_provider_sdk_calls",
            "maximum_provider_endpoint_connections",
            "maximum_provider_credentials_read",
            "maximum_api_keys_persisted",
            "maximum_tokens_persisted",
            "maximum_live_model_sessions",
            "maximum_tool_calls",
            "maximum_function_calls",
            "maximum_connector_calls",
            "maximum_actual_tool_executions",
            "maximum_deployments",
            "maximum_model_weight_changes",
        }:
            assert value == 0
