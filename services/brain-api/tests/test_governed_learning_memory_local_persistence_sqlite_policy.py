from __future__ import annotations

from scripts.lib.governed_learning_memory_local_persistence_authorization import (
    FUTURE_SQLITE_POLICY,
)
from test_governed_learning_memory_program_authorization import load_json


def test_future_sqlite_policy_is_strict_and_local_only() -> None:
    record = next(
        x
        for x in load_json("docs/governed-learning-memory/authorization-ledger.json")["records"]
        if x["authorization_transaction_id"] == "AION-223-GLM-0002"
    )
    assert record["sqlite_policy"] == FUTURE_SQLITE_POLICY
    assert record["prohibited_capabilities"]["database_path_inside_repository_enabled"] is False
    assert record["prohibited_capabilities"]["database_symlink_enabled"] is False
    assert record["prohibited_capabilities"]["arbitrary_sql_execution_enabled"] is False
    assert record["prohibited_capabilities"]["sqlite_extension_loading_enabled"] is False
    assert record["authorized_capabilities"]["database_file_mode_0600_approved"] is True
    assert (
        record["authorized_capabilities"]["update_rejection_triggers_approved"] is True
        and record["authorized_capabilities"]["delete_rejection_triggers_approved"] is True
    )
