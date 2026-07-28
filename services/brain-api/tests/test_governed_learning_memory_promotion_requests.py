from __future__ import annotations

from datetime import timedelta

import pytest
from knowledge_verified_memory_test_helpers import FIXED_TIME, sample_candidate
from pydantic import ValidationError
from test_governed_learning_memory_contracts import sample_promotion_request

from aion_brain.contracts import governed_learning_memory as glm


def test_promotion_request_is_operator_requested_dry_run_only():
    request = sample_promotion_request()

    assert request.operator_requested is True
    assert request.dry_run_only is True
    assert request.persistent_write_requested is False
    assert request.cognitive_memory_write_requested is False
    assert request.belief_mutation_requested is False
    assert request.automatic_promotion_requested is False
    assert request.runtime_effect is False


def test_promotion_request_rejects_duplicate_candidate_ids():
    candidate = sample_candidate()
    request = sample_promotion_request(candidate=candidate)
    payload = request.model_dump(mode="python")
    payload["candidate_ids"] = (candidate.candidate_id, candidate.candidate_id)
    payload["candidate_fingerprints"] = (
        candidate.candidate_fingerprint,
        candidate.candidate_fingerprint,
    )

    with pytest.raises(ValidationError):
        glm.KnowledgePromotionRequest.model_validate(payload)


def test_promotion_request_rejects_expiration_over_24_hours():
    candidate = sample_candidate()

    with pytest.raises(ValidationError):
        glm.build_knowledge_promotion_request(
            promotion_request_id="promotion-request-long-expiry",
            transaction_id="promotion-transaction-long-expiry",
            request_kind=glm.PromotionRequestKind.INITIAL_VERSION,
            candidate_ids=(candidate.candidate_id,),
            candidate_fingerprints=(candidate.candidate_fingerprint,),
            requested_projection_targets=(glm.MemoryProjectionTarget.SEMANTIC_MEMORY,),
            risk_class=glm.PromotionRiskClass.LOW,
            owner_scope_fingerprints=("a" * 64,),
            requested_at=FIXED_TIME,
            approval_evidence_ids=("approval-evidence-long-expiry",),
            expires_at=FIXED_TIME + timedelta(hours=25),
        )
