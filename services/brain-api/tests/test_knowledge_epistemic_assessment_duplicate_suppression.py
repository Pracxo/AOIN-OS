"""AION-211 duplicate suppression tests."""

from tests.test_knowledge_epistemic_assessment_helpers import (
    ControlledEpistemicAssessmentEngine,
    assessment_request,
    evidence_binding,
    graph_repository,
    single_claim,
    source_registry_repository,
)


def test_duplicate_evidence_group_is_suppressed() -> None:
    registry = source_registry_repository()
    graph = graph_repository(
        claims=(single_claim(),),
        bindings=(
            evidence_binding(binding_id="binding-0001"),
            evidence_binding(binding_id="binding-0002"),
        ),
        registry=registry,
    )
    batch = ControlledEpistemicAssessmentEngine().assess(
        request=assessment_request(),
        source_registry_repository=registry,
        claim_graph_repository=graph,
    )
    assert batch.assessments[0].duplicate_suppressed_count == 1
