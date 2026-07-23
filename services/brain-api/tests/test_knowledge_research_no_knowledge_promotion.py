from __future__ import annotations

from knowledge_research_test_helpers import valid_plan

from aion_brain.knowledge_intelligence.research import ControlledResearchAcquisitionService


def test_default_service_does_not_promote_knowledge():
    result = ControlledResearchAcquisitionService().run(valid_plan(adapter_type="disabled"))
    assert result.knowledge_candidate_created is False
    assert result.belief_created is False
    assert result.runtime_effect is False
