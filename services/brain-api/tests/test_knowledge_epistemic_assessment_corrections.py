"""AION-211 correction relation tests."""

from aion_brain.contracts.knowledge_claim_graph import ClaimRelationType
from aion_brain.knowledge_intelligence.epistemic_contradiction import assess_claim_relations
from tests.test_knowledge_claim_graph_helpers import relation


def test_correction_relation_is_recorded_without_effect() -> None:
    assessment = assess_claim_relations(
        claim_id="claim-0001",
        relations=(relation(relation_type=ClaimRelationType.CORRECTS),),
        structural_conflicts=(),
        independent_opposition_count=0,
    )
    assert assessment.correction_relation_ids == ("relation-0001",)
    assert assessment.contradiction_status == "none_detected"
