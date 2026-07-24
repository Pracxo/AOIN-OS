from __future__ import annotations

from knowledge_claim_graph_evaluation_test_helpers import (
    EPISTEMIC_AUTH_ID,
    active_authorization_record,
    assert_epistemic_authorization_rejects,
    validate_epistemic_authorization,
)


def test_epistemic_truth_authorization_exact_lifecycle_and_parentage():
    record = active_authorization_record()
    validate_epistemic_authorization(record)
    assert record["authorization_transaction_id"] == EPISTEMIC_AUTH_ID


def test_epistemic_truth_authorization_rejects_invalid_states():
    assert_epistemic_authorization_rejects(
        lambda record: record.update({"authorization_reusable": True})
    )
    assert_epistemic_authorization_rejects(
        lambda record: record.update({"authorization_consumed": True})
    )
    assert_epistemic_authorization_rejects(
        lambda record: record["authorized_capabilities"].update(
            {"explicit_abstention_approved": False}
        )
    )
    assert_epistemic_authorization_rejects(
        lambda record: record["prohibited_capabilities"].update(
            {"knowledge_promotion_enabled": True}
        )
    )
    assert_epistemic_authorization_rejects(
        lambda record: record["resource_limits"].update(
            {"maximum_persistent_assessment_write_batch": 1}
        )
    )
