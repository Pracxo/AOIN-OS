from __future__ import annotations

from datetime import timedelta

import pytest
from knowledge_research_test_helpers import NOW
from pydantic import ValidationError

from aion_brain.knowledge_intelligence.research_evidence import (
    ResearchIncidentRecord,
    ResearchOperatorReviewItem,
)


def test_incident_and_operator_review_are_redacted_and_bounded():
    incident = ResearchIncidentRecord(
        incident_id="research-incident-0001",
        plan_id="plan-001",
        severity="medium",
        reason_codes=("research_prompt_injection_untrusted",),
        redacted_summary="Instruction-like content was marked untrusted.",
        created_at=NOW,
        fingerprint="a" * 64,
    )
    review = ResearchOperatorReviewItem(
        review_item_id="research-review-item-0001",
        plan_id="plan-001",
        snapshot_ids=("source-snapshot-0001",),
        source_class_distribution={"official_standard": 1},
        policy_rejections=(),
        budget_status="within_budget",
        lineage_summary={"snapshot_count": 1},
        citation_reference_ids=("citation-reference-0001",),
        incident_ids=(incident.incident_id,),
        created_at=NOW,
        expires_at=NOW + timedelta(days=7),
        fingerprint="b" * 64,
    )
    assert review.operator_review_required is True
    assert review.knowledge_promotion_authorized is False
    with pytest.raises(ValidationError):
        ResearchIncidentRecord.model_validate(
            {**incident.model_dump(), "redacted_summary": "sk-secret"}
        )
    with pytest.raises(ValidationError):
        ResearchOperatorReviewItem.model_validate(
            {**review.model_dump(), "expires_at": NOW + timedelta(days=8)}
        )
