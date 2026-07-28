from __future__ import annotations

import json
from pathlib import Path

from scripts.lib import governed_learning_memory_local_persistence_operator_evaluation as eval225

REPO_ROOT = Path(__file__).resolve().parents[3]


def load_json(relative: str):
    return json.loads((REPO_ROOT / relative).read_text())


def test_engagement_resource_budgets_are_exact():
    auth = load_json("examples/governed-learning-memory/engagement-application-authorization.json")
    assert auth["resource_limits"] == eval225.AION226_RESOURCE_LIMITS
    assert auth["resource_limits"]["maximum_persistent_engagement_overlay_writes"] == 0
    assert auth["resource_limits"]["maximum_aion_224_store_writes"] == 0
