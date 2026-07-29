from __future__ import annotations

import json
from pathlib import Path

from scripts.lib import governed_learning_memory_local_persistence_operator_evaluation as eval225

REPO_ROOT = Path(__file__).resolve().parents[3]


def load_json(relative: str):
    return json.loads((REPO_ROOT / relative).read_text())


def test_aion224_delivery_is_reconciled_to_pr_140():
    ledger = load_json("docs/governed-learning-memory/program-ledger.json")
    delivery = ledger["aion_224_delivery"]
    assert delivery["feature_commits"] == [eval225.AION224_FEATURE_COMMIT]
    assert delivery["pull_requests"] == [140]
    assert delivery["merge_commits"] == [eval225.AION224_MERGE_COMMIT]
    assert delivery["ci_result"] == "pass"
    assert delivery["authorization_state"] == "consumed_by_AION-224_closed_by_AION-225"
