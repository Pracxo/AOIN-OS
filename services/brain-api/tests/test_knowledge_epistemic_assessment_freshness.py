"""AION-211 freshness tests."""

from tests.test_knowledge_claim_graph_helpers import MUCH_LATER
from tests.test_knowledge_epistemic_assessment_helpers import (
    ControlledEpistemicAssessmentEngine,
    assessment_request,
    graph_repository,
    source_registry_repository,
)


def test_stale_evidence_is_capped_and_reported() -> None:
    registry = source_registry_repository()
    graph = graph_repository(registry=registry)
    batch = ControlledEpistemicAssessmentEngine(clock=lambda: MUCH_LATER).assess(
        request=assessment_request(assessment_time=MUCH_LATER),
        source_registry_repository=registry,
        claim_graph_repository=graph,
    )
    assert batch.assessments[0].freshness_status == "stale"
    assert "epistemic_hard_cap_stale_evidence" in batch.assessments[0].reason_codes
