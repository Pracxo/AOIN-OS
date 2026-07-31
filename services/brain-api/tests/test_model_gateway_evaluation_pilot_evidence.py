from aion234_test_support import report


def test_pilot_evidence_fingerprint_and_counters_valid() -> None:
    payload = report()
    result = next(
        item
        for item in payload["scenario_results"]
        if item["scenario_id"] == "pilot_evidence_schema_and_fingerprint"
    )
    assert result["passed"] is True
    assert payload["pilot_validation"]["pilot_id"] == (
        "AION-233-controlled-model-gateway-simulation-pilot"
    )
    assert payload["pilot_validation"]["passed"] is True
    assert payload["pilot_validation"]["zero_effect_counters_passed"] is True
