from __future__ import annotations

import pytest
from pydantic import ValidationError
from test_knowledge_claim_graph_helpers import claim, relation, source_registry_repository

from aion_brain.contracts.knowledge_claim_graph import ClaimRelationType
from aion_brain.knowledge_intelligence.claim_graph import ClaimGraphProjectionError


def test_claim_relations_preserve_direction_and_reject_self_relation() -> None:
    edge = relation("claim-0002", "claim-0001", ClaimRelationType.SUPERSEDES)
    assert edge.source_claim_id == "claim-0002"
    assert edge.target_claim_id == "claim-0001"
    equivalent = relation("claim-0002", "claim-0001", ClaimRelationType.EQUIVALENT_TO)
    assert equivalent.source_claim_id == "claim-0001"
    with pytest.raises(ValidationError):
        relation("claim-0001", "claim-0001")


def test_revision_cycles_are_rejected() -> None:
    from aion_brain.knowledge_intelligence.claim_graph import ControlledTemporalClaimEvidenceGraph

    service = ControlledTemporalClaimEvidenceGraph()
    first = claim("claim-0001")
    second = claim("claim-0002")
    with pytest.raises(ClaimGraphProjectionError):
        service.project(
            claims=(first, second),
            evidence_bindings=(),
            relations=(
                relation("claim-0001", "claim-0002", ClaimRelationType.SUPERSEDES),
                relation("claim-0002", "claim-0001", ClaimRelationType.CORRECTS).model_copy(
                    update={"relation_id": "relation-0002"}
                ),
            ),
            source_registry_repository=source_registry_repository(),
        )
