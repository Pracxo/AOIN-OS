from __future__ import annotations

from test_governed_learning_memory_contracts import sample_transaction_context


def test_aion222_never_creates_or_decides_operator_approvals():
    context = sample_transaction_context()
    approvals = context.planner.validate_approval_evidence(
        approval_requests=context.approvals,
        approval_decisions=context.decisions,
        request=context.request,
        observed_at=context.approvals[0].created_at,
    )

    assert approvals.evidence_records[0].approval_creation_performed_by_aion222 is False
    assert approvals.evidence_records[0].approval_decision_performed_by_aion222 is False
