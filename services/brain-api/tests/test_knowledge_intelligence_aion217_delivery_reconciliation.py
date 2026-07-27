from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


def load_json(relative: str) -> dict[str, object]:
    return json.loads((REPO_ROOT / relative).read_text(encoding="utf-8"))


def test_aion217_delivery_reconciliation_is_exact() -> None:
    program = load_json("docs/knowledge-intelligence/program-ledger.json")
    tasks = {item["task_id"]: item for item in program["tasks"]}
    record = tasks["AION-217"]
    assert record["pull_requests"] == [131, 132]
    assert record["feature_commits"] == [
        "c27066e7de07a8539d0a7fec3eddf3c7d05d1615",
        "f703283e74adf1eb7a0ec88a5c7907a7527ce1e7",
        "ffd620e2e81d5c47140b851503515c724114633f",
    ]
    assert record["merge_commits"] == [
        "f1812bc2bc5f2af1a4fdc2eeaac12ab3c9aa4a1d",
        "262ea384800997edd0d46531ecb7ca44528e3745",
    ]
    assert record["authorization_state"] == "consumed_by_AION-217_closed_by_AION-218"
    assert record["evaluation_id"] == "AION-VKME-001"
