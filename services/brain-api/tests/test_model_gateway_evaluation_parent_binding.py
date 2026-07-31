from aion234_test_support import report, scenario


def test_parent_secure_runtime_binding_valid() -> None:
    payload = report()
    result = scenario(payload, "secure_runtime_parent_component_binding")
    assert result["passed"] is True
    assert payload["authorization_lineage"]["current_authorization_id"] == "AION-232-SRI-0002"
