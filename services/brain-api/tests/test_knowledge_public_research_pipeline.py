from __future__ import annotations

from public_research_pilot_test_helpers import run_simulation

from aion_brain.knowledge_intelligence.public_research_pilot import PIPELINE_PLANES


def test_pipeline_trace_contains_all_knowledge_planes() -> None:
    result = run_simulation()
    assert result.pipeline_trace.composed_planes == PIPELINE_PLANES
