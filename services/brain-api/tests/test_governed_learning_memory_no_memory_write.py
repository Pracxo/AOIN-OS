from __future__ import annotations

from test_governed_learning_memory_contracts import sample_planning_components


def test_memory_projection_records_never_write_cognitive_memory():
    components = sample_planning_components()

    assert components.projections.persistent_write_authorized is False
    assert components.projections.cognitive_memory_write_authorized is False
    assert all(record.memory_record_created is False for record in components.projections.records)
    assert all(
        record.cognitive_memory_written is False for record in components.projections.records
    )
