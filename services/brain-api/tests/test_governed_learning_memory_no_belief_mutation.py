from __future__ import annotations

from test_governed_learning_memory_program_authorization import load_json


def test_belief_creation_and_mutation_remain_disabled() -> None:
    auth = load_json("docs/governed-learning-memory/authorization-ledger.json")
    projection = load_json(
        "examples/governed-learning-memory/cognitive-memory-projection-plan.json"
    )

    assert auth["prohibited_capabilities"]["cognitive_belief_creation_enabled"] is False
    assert auth["prohibited_capabilities"]["cognitive_belief_mutation_enabled"] is False
    assert projection["belief_projection_candidate_plan_approved"] is True
    assert projection["cognitive_belief_mutation_enabled"] is False
    assert auth["resource_limits"]["maximum_belief_creations"] == 0
    assert auth["resource_limits"]["maximum_belief_mutations"] == 0
