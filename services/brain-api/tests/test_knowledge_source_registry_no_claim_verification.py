from __future__ import annotations

from knowledge_source_registry_implementation_helpers import valid_batch

from aion_brain.contracts.knowledge_source_registry import (
    SourceRegistryResourceUsage,
    evaluate_source_registry_budget,
)


def test_source_registry_never_verifies_claims_or_allows_claim_verification_budget():
    batch = valid_batch()
    assert all(record.claim_verified is False for record in batch.records)
    assert "claim_verified" in batch.model_dump_json()
    decision = evaluate_source_registry_budget(
        SourceRegistryResourceUsage(claim_verifications=1)
    )
    assert decision.within_budget is False
    assert "source_registry_claim_verification_blocked" in decision.reason_codes
