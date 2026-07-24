from __future__ import annotations

import pytest
from pydantic import ValidationError
from test_knowledge_claim_graph_helpers import (
    claim,
    evidence_binding,
    graph_batch,
    source_registry_repository,
)

from aion_brain.contracts.knowledge_claim_graph import ClaimEvidenceBinding
from aion_brain.knowledge_intelligence.claim_graph import ClaimGraphProjectionError


def test_evidence_binding_resolves_all_registry_record_kinds() -> None:
    service, registry, claims, _batch = graph_batch()
    batch = service.project(
        claims=claims,
        evidence_bindings=(
            evidence_binding(claims[0].claim_id),
            evidence_binding(claims[1].claim_id),
        ),
        relations=(),
        source_registry_repository=registry,
    )
    assert batch.evidence_binding_count == 2


def test_evidence_binding_rejects_missing_claim_and_missing_registry_reference() -> None:
    service, _registry, _claims, _batch = graph_batch()
    with pytest.raises(ClaimGraphProjectionError):
        service.project(
            claims=(claim("claim-0001"),),
            evidence_bindings=(evidence_binding("claim-missing"),),
            relations=(),
            source_registry_repository=source_registry_repository(),
        )
    bad = evidence_binding("claim-0001").model_copy(
        update={"source_registry_record_ids": ("missing-record",)}
    )
    with pytest.raises(ClaimGraphProjectionError):
        service.project(
            claims=(claim("claim-0001"),),
            evidence_bindings=(bad,),
            relations=(),
            source_registry_repository=source_registry_repository(),
        )
    with pytest.raises(ValidationError):
        ClaimEvidenceBinding.model_validate(
            {
                **evidence_binding().model_dump(mode="json"),
                "source_registry_record_ids": ("x", "x"),
            }
        )
