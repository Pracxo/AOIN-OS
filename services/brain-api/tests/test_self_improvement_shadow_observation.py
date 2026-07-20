"""AION-178 shadow observation tests."""

from __future__ import annotations

import pytest
from pydantic import ValidationError
from test_self_improvement_shadow_contracts import NOW, make_metric, make_reference, make_snapshot

from aion_brain.self_improvement.shadow_observation import observation_from_shadow_snapshot


@pytest.mark.parametrize(
    ("metric_name", "higher", "expected"),
    (
        ("retrieval_precision", True, "retrieval_failure"),
        ("plan_success", True, "planning_failure"),
        ("evidence_grounding", True, "evidence_grounding_failure"),
        ("policy_violation_count", False, "policy_block"),
        ("regression_count", False, "regression_drift"),
        ("improvement_survival", True, "generic_failure"),
    ),
)
def test_observation_problem_category_is_deterministic(
    metric_name: str,
    higher: bool,
    expected: str,
) -> None:
    reference = make_reference(repeated_count=2)
    metric = make_metric(
        metric_name=metric_name,
        reference_id=reference.reference_id,
        higher_is_better=higher,
    )
    snapshot = make_snapshot(reference=reference, metrics=(metric,))

    observation = observation_from_shadow_snapshot(
        snapshot,
        observation_id="shadow-observation-1",
        created_at=NOW,
    )

    assert observation.problem_category == expected
    assert observation.review_state == "shadow_observed"
    assert observation.runtime_effect is False


def test_observation_rejects_side_effect_state() -> None:
    observation = observation_from_shadow_snapshot(
        make_snapshot(),
        observation_id="shadow-observation-1",
        created_at=NOW,
    )
    payload = observation.model_dump(mode="python")
    payload["git_mutated"] = True

    with pytest.raises(ValidationError):
        type(observation)(**payload)
