from secure_runtime_aion232_test_helpers import active_authorization_record, authorization


def test_every_model_gateway_prohibited_capability_is_false() -> None:
    top_level = authorization()["model_gateway_prohibited_capabilities"]
    record = active_authorization_record()["prohibited_capabilities"]
    assert top_level == record
    assert all(value is False for value in top_level.values())
    for key in (
        "actual_model_provider_call_enabled",
        "provider_network_egress_enabled",
        "provider_credential_read_enabled",
        "api_key_persistence_enabled",
        "token_persistence_enabled",
        "tool_calling_enabled",
        "function_calling_enabled",
        "connector_execution_enabled",
        "production_runtime_authorized",
        "v02_release_ready",
    ):
        assert top_level[key] is False
