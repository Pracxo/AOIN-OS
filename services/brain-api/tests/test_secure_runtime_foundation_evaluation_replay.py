from secure_runtime_aion232_test_helpers import scenario


def test_replay_protection_is_exactly_once_and_fail_closed() -> None:
    reqs = scenario("replay_protection_exactly_once")["requirements"]
    assert reqs["first_valid_assertion_claimed"] is True
    assert reqs["exact_replay_rejected"] is True
    assert reqs["identifier_collision_preserved"] is True
    assert reqs["repository_unavailable_fails_closed"] is True
    assert reqs["schema_unavailable_fails_closed"] is True
    assert reqs["replay_key_derivation_deterministic"] is True
