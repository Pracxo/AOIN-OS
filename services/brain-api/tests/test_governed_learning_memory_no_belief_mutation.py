from __future__ import annotations

from test_governed_learning_memory_contracts import sample_planning_components

from aion_brain.contracts import governed_learning_memory as glm


def test_belief_candidate_projection_never_creates_or_mutates_beliefs():
    components = sample_planning_components(
        targets=(glm.MemoryProjectionTarget.BELIEF_CANDIDATE,),
        risk_class=glm.PromotionRiskClass.HIGH,
        approval_pairs=2,
    )

    assert components.projections.belief_mutation_authorized is False
    assert all(record.belief_created is False for record in components.projections.records)
    assert all(record.belief_mutated is False for record in components.projections.records)
