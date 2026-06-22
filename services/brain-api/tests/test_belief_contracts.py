from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from aion_brain.contracts.beliefs import (
    BeliefClaim,
    BeliefClaimCreateRequest,
    BeliefContradiction,
    BeliefQuery,
    BeliefSupport,
    TruthMaintenanceRequest,
)


def test_belief_claim_validates_confidence_bounds() -> None:
    with pytest.raises(ValidationError):
        BeliefClaim(
            claim_id="claim-1",
            claim_text="A generic claim is available",
            normalized_claim="a generic claim is available",
            claim_hash="hash",
            claim_type="generic",
            status="uncertain",
            confidence=1.2,
            sensitivity="internal",
            owner_scope=["workspace:main"],
            source_type="generic",
            observed_at=datetime.now(UTC),
        )


def test_belief_claim_rejects_chain_of_thought_content() -> None:
    with pytest.raises(ValidationError):
        BeliefClaimCreateRequest(
            claim_text="chain_of_thought: hidden text",
            source_type="generic",
            owner_scope=["workspace:main"],
        )


def test_belief_claim_create_request_validates_source_type() -> None:
    with pytest.raises(ValidationError):
        BeliefClaimCreateRequest(
            claim_text="A generic claim exists",
            source_type="finance",  # type: ignore[arg-type]
            owner_scope=["workspace:main"],
        )


def test_belief_support_validates_strength_bounds() -> None:
    with pytest.raises(ValidationError):
        BeliefSupport(
            support_id="support-1",
            claim_id="claim-1",
            support_type="evidence",
            source_type="evidence",
            source_id="evidence-1",
            relation_type="supports",
            strength=-0.1,
            confidence=0.5,
        )


def test_belief_contradiction_validates_severity() -> None:
    with pytest.raises(ValidationError):
        BeliefContradiction(
            contradiction_id="contradiction-1",
            claim_id="claim-1",
            source_type="generic",
            source_id="source-1",
            contradiction_type="generic",
            severity="urgent",  # type: ignore[arg-type]
            status="open",
            reason="conflict",
        )


def test_belief_query_rejects_empty_scope() -> None:
    with pytest.raises(ValidationError):
        BeliefQuery(scope=[])


def test_truth_maintenance_request_rejects_empty_owner_scope() -> None:
    with pytest.raises(ValidationError):
        TruthMaintenanceRequest(owner_scope=[])
