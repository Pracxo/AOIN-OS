from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
PROGRAM = REPO_ROOT / "docs/governed-learning-memory/program-ledger.json"


def test_aion228_delivery_is_reconcilable_to_pr145() -> None:
    program = json.loads(PROGRAM.read_text(encoding="utf-8"))
    delivery = program["aion_228_delivery"]
    assert delivery["task_id"] == "AION-228"
    assert delivery["branch"] == "phase/governed-learning-memory-controlled-local-continual-learning-pilot"
    assert delivery["authorization_transaction"] == "AION-227-GLM-0004"
    assert delivery["next_task"] == "AION-229"
    if delivery["pull_requests"]:
        assert delivery["pull_requests"] == [145]
    if delivery["feature_commits"]:
        assert delivery["feature_commits"] == [
            "07c146fe574a967266a2f2ad8b4473f51daf935d"
        ]
    if delivery["merge_commits"]:
        assert delivery["merge_commits"] == [
            "0fc95c345c1f8daada58a5b45e6f3b1fdd33d9e0"
        ]
