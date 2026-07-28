from __future__ import annotations

from scripts.lib.governed_learning_memory_local_persistence_authorization import (
    AION224_RESOURCE_LIMITS,
)
from test_governed_learning_memory_program_authorization import load_json


def test_future_local_persistence_budget_is_exact() -> None:
    record = next(
        x
        for x in load_json("docs/governed-learning-memory/authorization-ledger.json")["records"]
        if x["authorization_transaction_id"] == "AION-223-GLM-0002"
    )
    assert record["resource_limits"] == AION224_RESOURCE_LIMITS
