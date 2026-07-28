from __future__ import annotations

import json

from test_governed_learning_memory_contracts import REPO_ROOT


def test_aion221_authorization_is_reconciled_for_aion222():
    ledger = json.loads(
        (REPO_ROOT / "docs" / "governed-learning-memory" / "program-ledger.json").read_text(
            encoding="utf-8",
        )
    )
    authorization = json.loads(
        (REPO_ROOT / "docs" / "governed-learning-memory" / "authorization-ledger.json").read_text(
            encoding="utf-8"
        )
    )

    assert ledger["aion_221_delivery"]["pull_requests"] == [137]
    assert ledger["aion_221_delivery"]["merge_commits"] == [
        "ecb1e8ce8560ac06040cd297bfc26ff2ad020273"
    ]
    assert authorization["authorization_transaction_id"] == "AION-221-GLM-0001"
    assert authorization["authorized_task"] == "AION-222"
    assert authorization["authorization_active"] is True
