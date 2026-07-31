from aion234_test_support import report, scenario


def test_circuit_breaker_integrity_passes() -> None:
    assert scenario(report(), "circuit_breaker_integrity")["passed"] is True
