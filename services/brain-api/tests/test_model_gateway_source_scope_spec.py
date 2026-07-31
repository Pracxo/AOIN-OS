from secure_runtime_aion232_test_helpers import changed_paths_since_main, program


def test_aion233_implements_exact_model_gateway_source_scope() -> None:
    payload = program()
    expected = set(payload["model_gateway_future_source_scope"])
    changed = changed_paths_since_main()
    assert "services/brain-api/src/aion_brain/contracts/model_gateway.py" in expected
    assert "services/brain-api/src/aion_brain/model_gateway/provider_adapter.py" in expected
    assert expected <= changed
    assert payload["model_gateway_implemented"] is True
    assert (
        payload["aion_232_record"]["verification"]["no_aion_233_source_created_by_aion_232"]
        is True
    )
