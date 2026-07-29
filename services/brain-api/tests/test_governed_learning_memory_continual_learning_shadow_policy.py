from __future__ import annotations

from pathlib import Path

from scripts.lib import governed_learning_memory_continual_learning_pilot_authorization as auth227

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_shadow_policy_composes_aion226_without_persistence_or_factual_effect() -> None:
    auth = auth227.load_json(
        "examples/governed-learning-memory/continual-learning-pilot-authorization.json",
        REPO_ROOT,
    )
    policy = auth["shadow_policy"]
    assert policy["compose_aion_226_public_apis_only"] is True
    assert policy["overlays_in_memory_only"] is True
    assert policy["zero_active_overlays_after_close_required"] is True
    assert policy["persisted_knowledge_confidence_mutation_allowed"] is False
    assert policy["factual_status_mutation_allowed"] is False
