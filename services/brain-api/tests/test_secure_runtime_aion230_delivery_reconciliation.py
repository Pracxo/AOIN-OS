from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_aion230_delivery_reconciliation_is_recorded_for_aion231() -> None:
    program = json.loads(
        (REPO_ROOT / "docs/secure-runtime-integration/program-ledger.json").read_text()
    )

    delivery = program["aion_230_delivery"]
    assert delivery["feature_commits"] == ["710d2d49d09a99ab4cf30ae60a0dfe86468a0f78"]
    assert delivery["pull_requests"] == [148]
    assert delivery["merge_commits"] == ["f7f888ae36ea92c33ab261f0c1888c9ac2fe10af"]
    assert delivery["ci_result"] == "pass"
    assert delivery["authorization_state"] == "active_for_AION-231_formal_closeout_AION-232"
