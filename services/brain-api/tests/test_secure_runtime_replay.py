from __future__ import annotations

from tests.secure_runtime_test_support import secure_runtime_fixture


def test_exact_replay_is_rejected_after_initial_secure_runtime_claim() -> None:
    fixture = secure_runtime_fixture()

    second = fixture.pipeline.verify_once(fixture.assertion_envelope)

    assert second.result.outcome == "replay_detected"
    assert second.result.replay_detected is True
    assert second.result.verification_and_replay_checks_passed is False
