from secure_runtime_aion232_test_helpers import scenario


def test_offline_identity_and_public_key_boundary_fail_closed() -> None:
    offline = scenario("offline_ed25519_verification_integrity")["requirements"]
    for key in (
        "valid_assertion_verifies",
        "invalid_signature_rejects",
        "unknown_key_rejects",
        "revoked_key_rejects",
        "inactive_key_rejects",
        "retired_key_rejects",
        "wrong_issuer_rejects",
        "wrong_audience_rejects",
        "future_assertion_rejects",
        "expired_assertion_rejects",
        "overlong_assertion_lifetime_rejects",
    ):
        assert offline[key] is True
    registry = scenario("trusted_public_key_registry_boundary")["requirements"]
    assert registry["public_key_lookup_local_only"] is True
    assert registry["no_public_key_network_fetch"] is True
    assert registry["private_key_material_absent"] is True
