from __future__ import annotations

from scripts.lib.governed_learning_memory_local_persistence_authorization import (
    AION222_SOURCE_SCOPE,
    AION224_SOURCE_SCOPE,
)
from test_governed_learning_memory_program_authorization import REPO_ROOT, SCOPE, load_json


def test_authorization_scope_and_future_source_scope_are_recorded_only() -> None:
    auth = load_json("docs/governed-learning-memory/authorization-ledger.json")
    assert auth["authorization_scope"] == SCOPE
    assert auth["authorized_source_scope"] == AION224_SOURCE_SCOPE
    assert auth["aion_222_authorized_source_scope"] == AION222_SOURCE_SCOPE
    for relative in AION222_SOURCE_SCOPE:
        assert (REPO_ROOT / relative).exists(), relative
    for relative in AION224_SOURCE_SCOPE:
        if relative.endswith("__init__.py"):
            continue
        assert not (REPO_ROOT / relative).exists(), relative
