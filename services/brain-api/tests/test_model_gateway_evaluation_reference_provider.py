from aion234_test_support import report, scenario


def test_reference_provider_simulations_are_deterministic() -> None:
    payload = report()
    assert scenario(payload, "deterministic_text_reference_simulation")["passed"] is True
    assert scenario(payload, "deterministic_structured_reference_simulation")["passed"] is True
