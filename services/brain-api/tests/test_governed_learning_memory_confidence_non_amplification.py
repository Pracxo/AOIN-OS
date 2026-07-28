from __future__ import annotations

from test_governed_learning_memory_contracts import sample_planning_components


def test_projection_confidence_never_exceeds_version_confidence_cap():
    components = sample_planning_components()
    version = components.versions[0]
    projection = components.projections.records[0]

    assert projection.confidence_cap == version.candidate_confidence_cap
    assert projection.confidence_cap <= components.snapshots[0].candidate_confidence_cap
