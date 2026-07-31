from aion234_test_support import report, scenario


def test_response_validation_and_smuggling_rejection_pass() -> None:
    payload = report()
    response = scenario(payload, "response_validation_and_untrusted_output_classification")
    assert response["passed"] is True
    assert scenario(payload, "smuggled_action_and_executable_rejection")["passed"] is True
    assert response["evidence"]["untrusted_outputs_classified"] == 2
