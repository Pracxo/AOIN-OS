from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


def load_json(relative: str) -> dict[str, object]:
    return json.loads((REPO_ROOT / relative).read_text(encoding="utf-8"))


def report() -> dict[str, object]:
    return load_json(
        "examples/knowledge-intelligence/verified-memory-operator-evaluation-report.json"
    )


def test_engagement_is_non_factual_and_zero_effect() -> None:
    data = report()
    assert data["hard_gate_results"]["engagement_non_factuality_passed"] is True
    assert data["engagement_fact_promotions"] == 0
    assert data["engagement_confidence_effects"] == 0
    runtime = data["runtime_state"]
    assert runtime["engagement_signal_as_fact_enabled"] is False
    assert runtime["engagement_confidence_effect_enabled"] is False
