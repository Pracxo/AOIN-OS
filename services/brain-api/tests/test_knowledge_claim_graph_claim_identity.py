from __future__ import annotations

import pytest
from test_knowledge_claim_graph_helpers import (
    NOW,
    claim,
    evidence_binding,
    source_registry_repository,
    text_object,
)

from aion_brain.contracts.knowledge_claim_graph import ClaimModality, ClaimPolarity
from aion_brain.knowledge_intelligence.claim_graph import (
    ClaimGraphProjectionError,
    ControlledTemporalClaimEvidenceGraph,
)


def test_claim_identity_uses_structured_semantics_not_statement_text() -> None:
    first = claim("claim-0001", object_value=text_object("alpha"))
    second = claim("claim-0002", object_value=text_object("alpha"))
    changed = claim("claim-0003", object_value=text_object("beta"))
    negative = claim(
        "claim-0004", object_value=text_object("alpha"), polarity=ClaimPolarity.NEGATIVE
    )
    reported = claim(
        "claim-0005", object_value=text_object("alpha"), modality=ClaimModality.REPORTED
    )
    assert first.claim_identity_fingerprint == second.claim_identity_fingerprint
    assert first.claim_identity_fingerprint != changed.claim_identity_fingerprint
    assert first.claim_identity_fingerprint != negative.claim_identity_fingerprint
    assert first.claim_identity_fingerprint != reported.claim_identity_fingerprint


def test_identity_collision_for_same_claim_id_is_rejected() -> None:
    service = ControlledTemporalClaimEvidenceGraph(clock=lambda: NOW)
    first = claim("claim-0001", object_value=text_object("alpha"))
    changed = claim("claim-0001", object_value=text_object("beta"))
    with pytest.raises(ClaimGraphProjectionError):
        service.project(
            claims=(first, changed),
            evidence_bindings=(evidence_binding(first.claim_id),),
            relations=(),
            source_registry_repository=source_registry_repository(),
        )
