from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


def load_json(relative: str):
    return json.loads((REPO_ROOT / relative).read_text())


def test_path_scenario_records_isolation_and_cleanup():
    report = load_json(
        "examples/governed-learning-memory/local-persistence-operator-evaluation-report.json"
    )
    path_result = next(
        item
        for item in report["scenario_results"]
        if item["scenario_id"] == "explicit_initialization_and_path_isolation"
    )
    assert path_result["evidence"]["repository_path_rejected"] is True
    assert path_result["evidence"]["symlink_rejected"] is True
    assert path_result["evidence"]["database_file_mode"] == "0o600"
    assert report["retained_database_files"] == 0
