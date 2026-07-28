from __future__ import annotations

from test_governed_learning_memory_contracts import sample_planning_components

from aion_brain.contracts import governed_learning_memory as glm


def test_episodic_projection_is_planned_without_memory_write():
    components = sample_planning_components(
        transaction_id="promotion-transaction-episodic",
        targets=(glm.MemoryProjectionTarget.EPISODIC_MEMORY,),
    )
    record = components.projections.records[0]

    assert record.target is glm.MemoryProjectionTarget.EPISODIC_MEMORY
    assert record.projection_status is glm.MemoryProjectionStatus.PLANNED
    assert record.memory_record_created is False
    assert record.cognitive_memory_written is False
