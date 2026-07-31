from secure_runtime_aion232_test_helpers import active_authorization_record, authorization


def test_every_model_gateway_authorized_capability_is_true() -> None:
    top_level = authorization()["model_gateway_authorized_capabilities"]
    record = active_authorization_record()["authorized_capabilities"]
    assert top_level == record
    assert len(top_level) == 42
    assert all(value is True for value in top_level.values())
    assert top_level["model_gateway_contract_approved"] is True
    assert top_level["deterministic_reference_provider_approved"] is True
    assert top_level["simulation_only_model_gateway_approved"] is True
