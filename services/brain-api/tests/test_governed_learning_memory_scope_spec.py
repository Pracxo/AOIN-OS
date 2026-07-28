from __future__ import annotations

from test_governed_learning_memory_program_authorization import REPO_ROOT, SCOPE, load_json


def test_authorization_scope_and_future_source_scope_are_recorded_only() -> None:
    auth = load_json("docs/governed-learning-memory/authorization-ledger.json")

    assert auth["authorization_scope"] == SCOPE
    assert auth["authorized_source_scope"] == [
        "services/brain-api/src/aion_brain/contracts/governed_learning_memory.py",
        "services/brain-api/src/aion_brain/governed_learning_memory/__init__.py",
        "services/brain-api/src/aion_brain/governed_learning_memory/promotion_requests.py",
        "services/brain-api/src/aion_brain/governed_learning_memory/approval_evidence.py",
        "services/brain-api/src/aion_brain/governed_learning_memory/eligibility_revalidation.py",
        "services/brain-api/src/aion_brain/governed_learning_memory/knowledge_identity.py",
        "services/brain-api/src/aion_brain/governed_learning_memory/version_planning.py",
        "services/brain-api/src/aion_brain/governed_learning_memory/memory_projection.py",
        "services/brain-api/src/aion_brain/governed_learning_memory/promotion_transactions.py",
        "services/brain-api/src/aion_brain/governed_learning_memory/rollback.py",
        "services/brain-api/src/aion_brain/governed_learning_memory/integrity.py",
        "services/brain-api/src/aion_brain/governed_learning_memory/evidence.py",
    ]
    for relative in auth["authorized_source_scope"]:
        assert not (REPO_ROOT / relative).exists(), relative
