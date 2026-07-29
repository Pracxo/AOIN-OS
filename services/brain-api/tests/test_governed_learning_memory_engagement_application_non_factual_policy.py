from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


def load_json(relative: str):
    return json.loads((REPO_ROOT / relative).read_text())


def test_engagement_result_has_no_factual_or_confidence_effects():
    result = load_json("examples/governed-learning-memory/engagement-application-result.json")
    assert result["candidate_is_non_factual"] is True
    for key in [
        "factual_effect",
        "confidence_effect",
        "knowledge_effect",
        "source_independence_effect",
        "cognitive_memory_effect",
        "belief_effect",
        "production_policy_effect",
        "persistent_write_applied",
    ]:
        assert result[key] is False
