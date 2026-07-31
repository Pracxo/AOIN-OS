from aion234_test_support import report, scenario


def test_restricted_structured_schema_validation_passes() -> None:
    payload = report()
    assert scenario(payload, "restricted_structured_schema_validation")["passed"] is True
    assert scenario(payload, "deterministic_structured_reference_simulation")["passed"] is True
