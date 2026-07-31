from aion234_test_support import report, scenario


def test_request_idempotency_and_replay_controls_pass() -> None:
    result = scenario(report(), "request_envelope_and_idempotency")
    assert result["passed"] is True
    assert result["evidence"]["exact_replay"] is True
    assert result["evidence"]["changed_replay_rejected"] is True
