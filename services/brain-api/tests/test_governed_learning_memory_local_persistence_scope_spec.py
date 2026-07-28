from __future__ import annotations

from scripts.lib.governed_learning_memory_local_persistence_authorization import (
    AION224_AUTHORIZATION_SCOPE,
    AION224_SOURCE_SCOPE,
)
from test_governed_learning_memory_program_authorization import REPO_ROOT, load_json


def test_aion224_scope_is_exact_and_source_is_not_created() -> None:
    record = next(
        x
        for x in load_json("docs/governed-learning-memory/authorization-ledger.json")["records"]
        if x["authorization_transaction_id"] == "AION-223-GLM-0002"
    )
    assert (
        record["authorization_scope"] == AION224_AUTHORIZATION_SCOPE
        and record["authorized_source_scope"] == AION224_SOURCE_SCOPE
    )
    for relative in AION224_SOURCE_SCOPE:
        if relative.endswith("__init__.py"):
            continue
        assert not (REPO_ROOT / relative).exists(), relative
