from __future__ import annotations

from pathlib import Path

from scripts.lib import governed_learning_memory_continual_learning_pilot_authorization as auth227

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_aion228_resource_limits_are_exact_and_fail_closed_bounds_recorded() -> None:
    auth = auth227.load_json(
        "examples/governed-learning-memory/continual-learning-pilot-authorization.json",
        REPO_ROOT,
    )
    assert auth["resource_limits"] == auth227.RESOURCE_LIMITS
    assert auth["resource_limits"]["maximum_cycles_per_live_pilot"] == 3
    assert auth["resource_limits"]["maximum_retained_database_files"] == 0
    assert auth["resource_limits"]["maximum_model_weight_changes"] == 0
