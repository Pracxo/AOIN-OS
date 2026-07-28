from __future__ import annotations

from test_governed_learning_memory_program_authorization import load_json


def test_future_persistence_requires_new_dual_approval() -> None:
    record = next(
        x
        for x in load_json("docs/governed-learning-memory/authorization-ledger.json")["records"]
        if x["authorization_transaction_id"] == "AION-223-GLM-0002"
    )
    approval = record["approval_policy"]
    assert approval["minimum_independent_approvers"] == 2 and approval["required_roles"] == [
        "knowledge_steward",
        "memory_operator",
    ]
    assert (
        approval["plan_approval_can_authorize_persistence"] is False
        and approval["runtime_can_create_approval"] is False
    )
    assert (
        record["prohibited_capabilities"]["single_actor_persistent_write_enabled"] is False
        and record["prohibited_capabilities"]["approval_creation_by_runtime_enabled"] is False
    )
