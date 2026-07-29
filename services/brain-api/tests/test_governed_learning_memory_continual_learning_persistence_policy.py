from __future__ import annotations

from pathlib import Path

from scripts.lib import governed_learning_memory_continual_learning_pilot_authorization as auth227

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_persistence_policy_is_temporary_dual_approved_and_cleaned() -> None:
    auth = auth227.load_json(
        "examples/governed-learning-memory/continual-learning-pilot-authorization.json",
        REPO_ROOT,
    )
    policy = auth["persistence_policy"]
    assert policy["temporary_synthetic_store_only"] is True
    assert policy["knowledge_steward_approval_required"] is True
    assert policy["memory_operator_approval_required"] is True
    assert policy["single_actor_persistence_allowed"] is False
    assert policy["retained_store_allowed_after_close"] is False
