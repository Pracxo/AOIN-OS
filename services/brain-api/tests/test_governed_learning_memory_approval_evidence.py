from __future__ import annotations

from datetime import timedelta

from knowledge_verified_memory_test_helpers import FIXED_TIME
from test_governed_learning_memory_contracts import sample_approval_pair, sample_transaction_context

from aion_brain.contracts import governed_learning_memory as glm


def test_approval_evidence_projects_existing_approval_without_creation():
    context = sample_transaction_context()
    approval, decision = sample_approval_pair(context.request, context.candidate)
    evidence = glm.project_existing_approval_evidence(
        approval,
        decision,
        approval_evidence_id="approval-evidence-001",
        transaction_id=context.request.transaction_id,
        promotion_request_fingerprint=context.request.request_fingerprint,
        candidate_ids=context.request.candidate_ids,
        candidate_fingerprints=context.request.candidate_fingerprints,
        observed_at=FIXED_TIME + timedelta(minutes=2),
    )

    assert evidence.status is glm.ApprovalEvidenceStatus.VALID
    assert evidence.approval_creation_performed_by_aion222 is False
    assert evidence.approval_decision_performed_by_aion222 is False
    assert evidence.read_only is True
    assert evidence.runtime_effect is False
