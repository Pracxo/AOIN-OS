from __future__ import annotations

from pathlib import Path

from scripts.lib import governed_learning_memory_continual_learning_pilot_authorization as auth227

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_cycle_state_machine_is_closed_and_operator_gated() -> None:
    plan = auth227.load_json(
        "examples/governed-learning-memory/continual-learning-cycle-plan.json",
        REPO_ROOT,
    )
    assert tuple(plan["state_machine"]) == auth227.CYCLE_STATES
    assert plan["stage_skipping_allowed"] is False
    assert plan["automatic_transition_allowed"] is False
    assert plan["transition_after_expiry_allowed"] is False
