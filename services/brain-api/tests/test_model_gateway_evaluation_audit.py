from aion234_test_support import report, scenario


def test_audit_observability_health_integrity_pass() -> None:
    payload = report()
    audit = scenario(payload, "audit_chain_integrity")
    assert audit["passed"] is True
    assert scenario(payload, "observability_health_session_and_integrity")["passed"] is True
    assert audit["evidence"]["integrity"] == "passed"
    assert payload["model_gateway_integrity"]["audit_integrity"] == "passed"
