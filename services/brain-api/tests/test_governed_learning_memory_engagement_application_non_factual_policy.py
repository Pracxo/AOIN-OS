from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


def load_json(relative: str):
    return json.loads((REPO_ROOT / relative).read_text())


def test_engagement_result_has_no_factual_or_confidence_effects():
    result = load_json("examples/governed-learning-memory/engagement-application-result.json")
    assert all(
        item["candidate_is_non_factual"] is True
        for item in result["operator_review_items"]
    )
    assert all(
        item["factual_effect"] is False
        and item["confidence_effect"] is False
        and item["knowledge_effect"] is False
        and item["production_policy_effect"] is False
        for item in result["counterfactual_results"]
    )
    for key in [
        "persistent_engagement_overlay_writes",
        "aion_224_store_writes",
        "production_policy_mutations",
        "cognitive_memory_writes",
        "actual_belief_creations",
        "actual_belief_mutations",
    ]:
        assert result[key] == 0
