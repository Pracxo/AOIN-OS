from __future__ import annotations

from datetime import timedelta

import pytest
from knowledge_verified_memory_test_helpers import FIXED_TIME
from test_governed_learning_memory_contracts import sample_approval_pair, sample_transaction_context

from aion_brain.contracts import governed_learning_memory as glm


def test_expired_approval_evidence_is_rejected():
    context = sample_transaction_context()
    approval, decision = sample_approval_pair(
        context.request,
        context.candidate,
        expires_delta=timedelta(minutes=1),
    )

    with pytest.raises(ValueError):
        glm.project_existing_approval_evidence(
            approval,
            decision,
            approval_evidence_id="approval-evidence-expired",
            transaction_id=context.request.transaction_id,
            promotion_request_fingerprint=context.request.request_fingerprint,
            candidate_ids=context.request.candidate_ids,
            candidate_fingerprints=context.request.candidate_fingerprints,
            observed_at=FIXED_TIME + timedelta(minutes=2),
        )
