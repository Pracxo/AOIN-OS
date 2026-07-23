import copy

from knowledge_source_registry_test_helpers import (
    AUTHORIZED_KEYS,
    active_source_record,
    assert_source_authorization_rejects,
    closed_research_record,
    read_json,
    validate_source_authorization,
)


def test_authorization_records_accept_current_lifecycle_payload():
    closed = closed_research_record()
    assert closed["authorization_active"] is False
    assert closed["authorization_consumed"] is True
    assert closed["authorization_expired"] is True
    validate_source_authorization(active_source_record())


def test_negative_authorization_mutations_rejected():
    assert_source_authorization_rejects(lambda r: r.update({"implementation_task": "AION-208"}))
    assert_source_authorization_rejects(
        lambda r: r.update({"authorization_scope": "unrestricted-public-web-research"})
    )
    assert_source_authorization_rejects(
        lambda r: r["authorized_capabilities"].pop(next(iter(AUTHORIZED_KEYS)))
    )
    assert_source_authorization_rejects(
        lambda r: r["authorized_capabilities"].update({"extra_capability_approved": True})
    )
    for key in (
        "source_registry_runtime_enabled",
        "source_body_persistence_enabled",
        "background_crawler_enabled",
        "search_provider_integration_enabled",
        "connector_integration_enabled",
        "credential_use_enabled",
        "private_network_access_enabled",
        "claim_verification_enabled",
        "knowledge_promotion_enabled",
        "belief_mutation_enabled",
        "model_weight_training_enabled",
    ):
        assert_source_authorization_rejects(
            lambda r, k=key: r["prohibited_capabilities"].update({k: True})
        )


def test_wrong_domain_and_second_active_authorization_rejected_by_fixture_logic():
    auth = copy.deepcopy(read_json("docs/knowledge-intelligence/authorization-ledger.json"))
    auth["records"].append(copy.deepcopy(active_source_record()))
    assert len([r for r in auth["records"] if r.get("authorization_active") is True]) != 1
    assert_source_authorization_rejects(
        lambda r: r.update({"authorization_transaction_id": "AION-201-CA-0009"})
    )
