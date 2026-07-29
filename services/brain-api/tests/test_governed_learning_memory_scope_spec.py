from __future__ import annotations

from scripts.lib.governed_learning_memory_local_persistence_authorization import (
    AION222_SOURCE_SCOPE,
    AION224_SOURCE_SCOPE,
    ENGAGEMENT_APPLICATION_AUTHORIZED_STATE,
    ENGAGEMENT_APPLICATION_IMPLEMENTED_STATE,
    IMPLEMENTED_PENDING_CLOSEOUT_STATE,
)
from test_governed_learning_memory_program_authorization import REPO_ROOT, SCOPE, load_json


def test_authorization_scope_and_future_source_scope_are_recorded_only() -> None:
    auth = load_json("docs/governed-learning-memory/authorization-ledger.json")
    engagement_states = {
        ENGAGEMENT_APPLICATION_AUTHORIZED_STATE,
        ENGAGEMENT_APPLICATION_IMPLEMENTED_STATE,
    }
    if auth["program_state"] in engagement_states:
        record = next(
            item
            for item in auth["records"]
            if item["authorization_transaction_id"] == "AION-223-GLM-0002"
        )
        assert record["authorization_scope"] == SCOPE
        assert record["authorized_source_scope"] == AION224_SOURCE_SCOPE
    else:
        assert auth["authorization_scope"] == SCOPE
        assert auth["authorized_source_scope"] == AION224_SOURCE_SCOPE
    assert auth["aion_222_authorized_source_scope"] == AION222_SOURCE_SCOPE
    for relative in AION222_SOURCE_SCOPE:
        assert (REPO_ROOT / relative).exists(), relative
    implemented = auth["program_state"] in {
        IMPLEMENTED_PENDING_CLOSEOUT_STATE,
        ENGAGEMENT_APPLICATION_AUTHORIZED_STATE,
        ENGAGEMENT_APPLICATION_IMPLEMENTED_STATE,
    }
    for relative in AION224_SOURCE_SCOPE:
        if relative.endswith("__init__.py"):
            continue
        assert (REPO_ROOT / relative).exists() is implemented, relative
