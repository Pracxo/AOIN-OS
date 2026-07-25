"""AION-211 scorecard tests."""

from decimal import Decimal

from aion_brain.contracts.knowledge_epistemic_assessment import default_scorecard_policy


def test_scorecard_policy_is_versioned_and_weighted() -> None:
    policy = default_scorecard_policy()
    assert policy.scorecard_version == "aion-epistemic-scorecard/v1"
    assert sum(policy.weights.values(), Decimal("0")) == Decimal("1.000000")
    assert policy.minimum_independent_support_groups == 2
