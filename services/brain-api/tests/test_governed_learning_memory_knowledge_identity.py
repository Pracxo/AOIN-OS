from __future__ import annotations

from test_governed_learning_memory_contracts import sample_planning_components

from aion_brain.contracts import governed_learning_memory as glm


def test_knowledge_identity_is_deterministic_and_not_persisted():
    first = sample_planning_components(transaction_id="promotion-transaction-identity-a")
    second = sample_planning_components(transaction_id="promotion-transaction-identity-b")

    assert first.identities[0].knowledge_identity_id == second.identities[0].knowledge_identity_id
    assert first.identities[0].disposition is glm.KnowledgeIdentityDisposition.NEW_IDENTITY
    assert first.identities[0].persistent_identity_created is False
    assert first.identities[0].runtime_effect is False
