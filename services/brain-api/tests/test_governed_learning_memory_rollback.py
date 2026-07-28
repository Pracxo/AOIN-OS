from __future__ import annotations

from test_governed_learning_memory_contracts import sample_planning_components


def test_rollback_plan_is_reviewable_and_non_executing():
    components = sample_planning_components()
    rollback = components.rollback

    assert rollback.valid is True
    assert rollback.step_count == len(rollback.steps)
    assert rollback.runtime_effect is False
    assert all(step.actual_execution is False for step in rollback.steps)
    assert all(step.persistent_write_applied is False for step in rollback.steps)
