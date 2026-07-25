"""AION-211 in-memory query tests."""

from aion_brain.contracts.knowledge_epistemic_assessment import EpistemicAssessmentQuery
from aion_brain.knowledge_intelligence.epistemic_assessment import (
    ControlledEpistemicAssessmentEngine,
)
from tests.test_knowledge_epistemic_assessment_helpers import assessment_batch


def test_query_filters_in_memory_batch() -> None:
    batch = assessment_batch()
    result = ControlledEpistemicAssessmentEngine().query(
        batch=batch,
        query=EpistemicAssessmentQuery(claim_id="claim-0001", status="supported"),
    )
    assert result.result_count == 1
    assert result.runtime_effect is False
