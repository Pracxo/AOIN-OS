from __future__ import annotations

import json

from test_governed_learning_memory_contracts import REPO_ROOT


def test_current_state_marks_local_persistence_authorized_not_implemented():
    ledger = json.loads(
        (REPO_ROOT / "docs/governed-learning-memory/program-ledger.json").read_text(
            encoding="utf-8"
        )
    )
    assert ledger["current_authorization"]["authorization_transaction_id"] == "AION-223-GLM-0002"
    assert ledger["current_authorization"]["authorized_task"] == "AION-224"
    assert ledger["knowledge_promotion_transaction_core"]["implemented"] is True
    assert ledger["knowledge_promotion_transaction_core"]["runtime_writes_enabled"] is False
    assert ledger["promotion_transaction_operator_evaluation_passed"] is True
    assert ledger["local_append_only_knowledge_store_authorized"] is True
    assert ledger["local_append_only_knowledge_store_implemented"] is False
    assert ledger["operator_invoked_local_persistence_available"] is False
