from secure_runtime_aion232_test_helpers import changed_paths_since_main, report


def test_aion232_records_future_source_scope_without_changing_runtime_source() -> None:
    payload = report()
    assert (
        "services/brain-api/src/aion_brain/contracts/model_gateway.py"
        in payload["future_model_gateway_source_scope"]
    )
    changed = changed_paths_since_main()
    assert not any(
        path == "services/brain-api/src/aion_brain/contracts/model_gateway.py"
        or path.startswith("services/brain-api/src/aion_brain/model_gateway/")
        for path in changed
    )
    assert payload["repository_integrity"]["no_aion_233_source_added_on_aion_232_branch"] is True
