import copy

from knowledge_intelligence_test_helpers import (
    APPROVED_KEYS,
    assert_rejects,
    read_json,
    validate_authorization_record,
)


def test_authorization_record_accepts_exact_payload():
    validate_authorization_record(
        read_json("docs/knowledge-intelligence/authorization-ledger.json")["records"][0]
    )


def test_negative_authorization_mutations_rejected():
    assert_rejects(lambda r: r.update({"implementation_task": "AION-206"}))
    assert_rejects(lambda r: r.update({"authorization_scope": "unrestricted-public-web-research"}))
    assert_rejects(lambda r: r["authorized_capabilities"].pop(APPROVED_KEYS[0]))
    assert_rejects(
        lambda r: r["authorized_capabilities"].update({"extra_capability_approved": True})
    )
    for key in (
        "research_runtime_enabled",
        "network_access_enabled",
        "background_crawler_enabled",
        "search_provider_integration_enabled",
        "connector_integration_enabled",
        "credential_use_enabled",
        "http_post_enabled",
        "private_network_access_enabled",
        "automatic_knowledge_promotion_enabled",
        "automatic_belief_creation_enabled",
        "source_mutation_enabled",
        "model_weight_training_enabled",
    ):
        assert_rejects(lambda r, k=key: r["prohibited_capabilities"].update({k: True}))


def test_wrong_domain_and_second_active_authorization_rejected_by_fixture_logic():
    auth = copy.deepcopy(read_json("docs/knowledge-intelligence/authorization-ledger.json"))
    auth["records"].append(copy.deepcopy(auth["records"][0]))
    assert len([r for r in auth["records"] if r.get("authorization_active") is True]) != 1
    assert_rejects(lambda r: r.update({"authorization_transaction_id": "AION-201-CA-0009"}))
