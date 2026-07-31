from aion234_test_support import report, scenario


def test_routing_fallback_and_retry_are_planning_only() -> None:
    payload = report()
    assert scenario(payload, "deterministic_routing_and_model_selection")["passed"] is True
    assert scenario(payload, "fallback_and_retry_planning_only")["passed"] is True
