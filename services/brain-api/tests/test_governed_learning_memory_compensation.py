from __future__ import annotations

from test_governed_learning_memory_contracts import sample_planning_components


def test_compensation_plan_is_review_item_only_and_non_executing():
    components = sample_planning_components()
    compensation = components.compensation

    assert compensation.valid is True
    assert compensation.step_count == len(compensation.steps)
    assert compensation.runtime_effect is False
    assert compensation.steps[0].operation == "create_operator_review_item"
    assert compensation.steps[0].actual_execution is False
