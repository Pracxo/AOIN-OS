from __future__ import annotations

from test_knowledge_claim_graph_helpers import claim, text_object

from aion_brain.contracts.knowledge_claim_graph import ClaimPolarity
from aion_brain.knowledge_intelligence.claim_graph import ControlledTemporalClaimEvidenceGraph


def test_structural_conflicts_do_not_resolve_contradictions() -> None:
    service = ControlledTemporalClaimEvidenceGraph()
    candidates = service.detect_structural_conflicts(
        (
            claim("claim-0001", object_value=text_object("alpha")),
            claim("claim-0002", object_value=text_object("alpha"), polarity=ClaimPolarity.NEGATIVE),
        )
    )
    assert candidates[0].contradiction_resolved is False
    assert candidates[0].left_claim_false is False
    assert candidates[0].right_claim_false is False
