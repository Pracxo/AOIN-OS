from __future__ import annotations

import json

from test_governed_learning_memory_contracts import REPO_ROOT


def test_current_state_marks_promotion_transaction_core_implemented_write_disabled():
    ledger = json.loads(
        (REPO_ROOT / "docs" / "governed-learning-memory" / "program-ledger.json").read_text(
            encoding="utf-8",
        )
    )

    assert ledger["program_id"] == "AION-GOVERNED-LEARNING-MEMORY-001"
    assert ledger["current_authorization"]["authorization_transaction_id"] == "AION-221-GLM-0001"
    assert ledger["current_authorization"]["authorized_task"] == "AION-222"
    assert ledger["knowledge_promotion_transaction_core"]["implemented"] is True
    assert ledger["knowledge_promotion_transaction_core"]["runtime_writes_enabled"] is False
