from __future__ import annotations

from test_governed_learning_memory_contracts import sample_planning_components

from aion_brain.contracts import governed_learning_memory as glm


def test_belief_candidate_projection_is_candidate_only_without_belief_mutation():
    components = sample_planning_components(
        transaction_id="promotion-transaction-belief",
        targets=(glm.MemoryProjectionTarget.BELIEF_CANDIDATE,),
        risk_class=glm.PromotionRiskClass.HIGH,
        approval_pairs=2,
    )
    record = components.projections.records[0]

    assert record.target is glm.MemoryProjectionTarget.BELIEF_CANDIDATE
    assert record.projection_status is glm.MemoryProjectionStatus.PLANNED
    assert record.belief_created is False
    assert record.belief_mutated is False
    assert "belief_projection_is_candidate_only" in record.reason_codes
