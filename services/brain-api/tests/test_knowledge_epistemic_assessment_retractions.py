"""AION-211 retraction relation tests."""

from aion_brain.contracts.knowledge_claim_graph import ClaimRelationType
from tests.test_knowledge_claim_graph_helpers import relation
from tests.test_knowledge_epistemic_assessment_helpers import (
    ControlledEpistemicAssessmentEngine,
    assessment_request,
    graph_claims,
    graph_repository,
    source_registry_repository,
)


def test_retraction_relation_forces_retracted_status() -> None:
    registry = source_registry_repository()
    graph = graph_repository(
        claims=graph_claims(),
        relations=(relation(relation_type=ClaimRelationType.RETRACTS),),
        registry=registry,
    )
    batch = ControlledEpistemicAssessmentEngine().assess(
        request=assessment_request(),
        source_registry_repository=registry,
        claim_graph_repository=graph,
    )
    assessment = batch.assessments[0]
    assert assessment.status == "retracted"
    assert assessment.knowledge_promoted is False
