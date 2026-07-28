from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


def load_json(relative: str):
    return json.loads((REPO_ROOT / relative).read_text())


def test_replay_scenarios_record_idempotency_and_changed_replay_rejection():
    report = load_json(
        "examples/governed-learning-memory/local-persistence-operator-evaluation-report.json"
    )
    idem = next(
        row for row in report["scenario_results"] if row["scenario_id"] == "idempotent_exact_replay"
    )
    changed = next(
        row
        for row in report["scenario_results"]
        if row["scenario_id"] == "changed_replay_and_collision_rejection"
    )
    assert idem["evidence"]["new_ledger_events"] == 0
    assert changed["evidence"]["same_transaction_id_changed_request_rejected"] is True
    assert report["synthetic_changed_replays_rejected"] == 1
