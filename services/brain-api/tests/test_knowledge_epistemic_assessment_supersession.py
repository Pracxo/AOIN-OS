"""AION-211 supersession relation tests."""

from aion_brain.contracts.knowledge_claim_graph import ClaimRelationType
from tests.test_knowledge_claim_graph_helpers import relation
from tests.test_knowledge_epistemic_assessment_helpers import (
    ControlledEpistemicAssessmentEngine,
    assessment_request,
    graph_claims,
    graph_repository,
    source_registry_repository,
)


def test_supersession_relation_forces_superseded_status_without_current_support() -> None:
    registry = source_registry_repository()
    graph = graph_repository(
        claims=graph_claims(),
        relations=(relation(relation_type=ClaimRelationType.SUPERSEDES),),
        registry=registry,
    )
    batch = ControlledEpistemicAssessmentEngine().assess(
        request=assessment_request(),
        source_registry_repository=registry,
        claim_graph_repository=graph,
    )
    assert batch.assessments[0].status == "superseded"
