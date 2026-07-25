"""AION-211 role ambiguity tests."""

from aion_brain.contracts.knowledge_claim_graph import EvidenceRole
from tests.test_knowledge_epistemic_assessment_helpers import (
    ControlledEpistemicAssessmentEngine,
    assessment_request,
    evidence_binding,
    graph_repository,
    single_claim,
    source_registry_repository,
)


def test_same_group_support_and_opposition_is_ambiguous() -> None:
    registry = source_registry_repository()
    graph = graph_repository(
        claims=(single_claim(),),
        bindings=(
            evidence_binding(binding_id="binding-0001"),
            evidence_binding(binding_id="binding-0002", evidence_role=EvidenceRole.OPPOSES),
        ),
        registry=registry,
    )
    batch = ControlledEpistemicAssessmentEngine().assess(
        request=assessment_request(),
        source_registry_repository=registry,
        claim_graph_repository=graph,
    )
    assert batch.assessments[0].ambiguous_group_count == 2
    assert batch.assessments[0].independent_support_count == 0
