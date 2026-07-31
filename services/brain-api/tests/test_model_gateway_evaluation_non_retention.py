from aion234_test_support import report, scenario


def test_message_context_and_output_non_retention_boundaries() -> None:
    payload = report()
    assert scenario(payload, "message_context_normalization_and_non_retention")["passed"] is True
    assert scenario(payload, "system_instruction_policy_and_protected_material")["passed"] is True
    assert scenario(payload, "output_provenance_and_redaction")["passed"] is True
    assert payload["redacted"] is True
