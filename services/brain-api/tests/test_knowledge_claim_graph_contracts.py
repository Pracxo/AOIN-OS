from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError
from test_knowledge_claim_graph_helpers import (
    claim,
    evidence_binding,
    graph_batch,
    relation,
)

from aion_brain.contracts.knowledge_claim_graph import (
    ClaimEvidenceBinding,
    ClaimGraphRecordEnvelope,
    ClaimRelationEdge,
)


def test_valid_contracts_accept_explicit_unverified_graph_shapes() -> None:
    service, registry, claims, batch = graph_batch()
    assert claims[0].unverified is True
    assert evidence_binding(claims[0].claim_id).verified_support is False
    assert relation().truth_effect is False
    assert batch.budget_decision.budget.maximum_graph_write_batch == 0
    report = service.audit(
        service.simulate_append(
            __import__(
                "aion_brain.knowledge_intelligence.claim_graph_repository",
                fromlist=["InMemoryTemporalClaimGraphRepository"],
            ).InMemoryTemporalClaimGraphRepository(),
            batch,
        )[0],
        source_registry_repository=registry,
    )
    assert report.status.value == "passed"


def test_extra_fields_malformed_fingerprints_and_wrong_lineage_are_rejected() -> None:
    with pytest.raises(ValidationError):
        ClaimEvidenceBinding.model_validate(
            {**evidence_binding().model_dump(mode="json"), "extra": "blocked"}
        )
    with pytest.raises(ValidationError):
        ClaimRelationEdge.model_validate(
            {**relation().model_dump(mode="json"), "relation_fingerprint": "abc"}
        )
    with pytest.raises(ValidationError):
        ClaimGraphRecordEnvelope.model_validate(
            {
                **graph_batch()[3].records[0].model_dump(mode="json"),
                "authorization_transaction_id": "AION-208-KI-9999",
            }
        )


def test_naive_and_non_utc_timestamps_are_rejected_and_models_are_immutable() -> None:
    with pytest.raises(ValidationError):
        claim(transaction_time=datetime(2026, 1, 1))
    with pytest.raises(ValidationError):
        claim(transaction_time=datetime(2026, 1, 1, tzinfo=timezone(timedelta(hours=1))))
    item = claim()
    with pytest.raises(ValidationError):
        item.verified = True  # type: ignore[misc]
    with pytest.raises(ValidationError):
        type(item).model_validate({**item.model_dump(mode="json"), "runtime_effect": True})
