from knowledge_source_registry_test_helpers import (
    AUTHORIZED_KEYS,
    RESOURCE_LIMITS,
    active_source_record,
    assert_source_authorization_rejects,
    validate_source_authorization,
)


def test_source_registry_authorization_accepts_exact_payload():
    validate_source_authorization(active_source_record())


def test_source_registry_authorization_rejects_scope_and_flag_mutations():
    assert_source_authorization_rejects(lambda r: r.update({"implementation_task": "AION-208"}))
    assert_source_authorization_rejects(
        lambda r: r.update({"authorization_scope": "source-body-store"})
    )
    assert_source_authorization_rejects(
        lambda r: r["authorized_capabilities"].pop(next(iter(AUTHORIZED_KEYS)))
    )
    assert_source_authorization_rejects(
        lambda r: r["authorized_capabilities"].update({"extra_capability_approved": True})
    )
    assert_source_authorization_rejects(
        lambda r: r["resource_limits"].update({"maximum_network_calls": 1})
    )
    for key in (
        "source_registry_runtime_enabled",
        "source_body_persistence_enabled",
        "public_network_fetch_enabled",
        "claim_verification_enabled",
        "knowledge_promotion_enabled",
        "belief_mutation_enabled",
        "api_route_approved",
        "migration_approved",
        "dependency_change_approved",
    ):
        assert_source_authorization_rejects(
            lambda r, k=key: r["prohibited_capabilities"].update({k: True})
        )
    assert active_source_record()["resource_limits"] == RESOURCE_LIMITS
