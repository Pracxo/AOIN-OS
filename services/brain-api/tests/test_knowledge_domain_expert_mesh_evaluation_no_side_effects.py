from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_domain_mesh_evaluation_report_records_zero_side_effects() -> None:
    report = json.loads(
        (
            REPO_ROOT
            / "examples/knowledge-intelligence/domain-expert-mesh-operator-evaluation-report.json"
        )
        .read_text(encoding="utf-8")
    )
    integrity = report["repository_integrity"]
    assert integrity["repository_unchanged"] is True
    for key, value in integrity.items():
        if key == "repository_unchanged":
            continue
        if isinstance(value, int) and not isinstance(value, bool):
            assert value == 0, key

    runtime = report["runtime_state"]
    assert runtime["runtime_effect"] is False
    assert runtime["tool_fabric_implemented"] is False
    assert runtime["actual_tool_executed"] is False
    assert runtime["network_called"] is False
    assert runtime["persistent_mesh_write_applied"] is False
