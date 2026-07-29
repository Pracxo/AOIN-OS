from __future__ import annotations

import pytest
from governed_engagement_learning_test_helpers import (
    EXPIRES_AT,
    FIXED_NOW,
    build_synthetic_shadow_pilot_inputs,
)

from aion_brain.contracts.approvals import ApprovalDecision
from aion_brain.contracts.governed_engagement_learning import engagement_fingerprint


def _approval_context():
    inputs = build_synthetic_shadow_pilot_inputs()
    service = inputs.service
    bindings = service.bind_candidates(
        signal_batch=inputs.signal_batch,
        candidates=inputs.candidates,
        observed_at=FIXED_NOW,
        valid_until=EXPIRES_AT,
    )
    risks = service.classify_risk(bindings, assessed_at=FIXED_NOW)
    identities = service.derive_adaptation_identities(bindings)
    baseline = service.build_baseline_snapshot(
        bindings=bindings,
        fixture_fingerprint=inputs.fixture_fingerprint,
        captured_at=FIXED_NOW,
    )
    overlay_fingerprints = {
        binding.learning_candidate_id: engagement_fingerprint(
            {
                "candidate": binding.candidate_fingerprint,
                "baseline": baseline.snapshot_fingerprint,
                "fixture": inputs.fixture_fingerprint,
            }
        )
        for binding in bindings
    }
    rollback_fingerprints = {
        binding.learning_candidate_id: engagement_fingerprint(
            {
                "rollback": binding.candidate_fingerprint,
                "fixture": inputs.fixture_fingerprint,
            }
        )
        for binding in bindings
    }
    return (
        inputs,
        bindings,
        risks,
        identities,
        baseline,
        overlay_fingerprints,
        rollback_fingerprints,
    )


def test_existing_approval_evidence_projects_exact_bindings():
    (
        inputs,
        bindings,
        risks,
        identities,
        baseline,
        overlay_fingerprints,
        rollback_fingerprints,
    ) = _approval_context()

    bundles = inputs.service.validate_approvals(
        approval_records=inputs.approval_records,
        bindings=bindings,
        risk_assessments=risks,
        identities=identities,
        baseline_snapshot=baseline,
        fixture_fingerprint=inputs.fixture_fingerprint,
        overlay_fingerprints=overlay_fingerprints,
        rollback_fingerprints=rollback_fingerprints,
        overlay_expires_at=EXPIRES_AT,
    )

    assert len(bundles) == 9
    assert {bundle.approval_status for bundle in bundles} == {"approved"}
    assert all(bundle.separation_of_duties_passed for bundle in bundles)
    for bundle in bundles:
        for evidence in bundle.evidence_records:
            assert evidence.candidate_id in {binding.learning_candidate_id for binding in bindings}
            assert evidence.fixture_fingerprint == inputs.fixture_fingerprint
            assert evidence.approval_creation_performed_by_aion226 is False
            assert evidence.approval_decision_performed_by_aion226 is False
            assert evidence.runtime_effect is False


def test_approval_payload_mismatch_expiry_and_separation_of_duties_are_rejected():
    (
        inputs,
        bindings,
        risks,
        identities,
        baseline,
        overlay_fingerprints,
        rollback_fingerprints,
    ) = _approval_context()
    candidate_id = bindings[0].learning_candidate_id

    bad_payload_records = dict(inputs.approval_records)
    bad_request, bad_decision = bad_payload_records[candidate_id][0]
    bad_payload = dict(bad_request.payload)
    bad_payload["fixture_fingerprint"] = "0" * 64
    bad_payload_records[candidate_id] = (
        (bad_request.model_copy(update={"payload": bad_payload}), bad_decision),
    )
    with pytest.raises(ValueError):
        inputs.service.validate_approvals(
            approval_records=bad_payload_records,
            bindings=bindings,
            risk_assessments=risks,
            identities=identities,
            baseline_snapshot=baseline,
            fixture_fingerprint=inputs.fixture_fingerprint,
            overlay_fingerprints=overlay_fingerprints,
            rollback_fingerprints=rollback_fingerprints,
            overlay_expires_at=EXPIRES_AT,
        )

    expired_records = dict(inputs.approval_records)
    expired_request, expired_decision = expired_records[candidate_id][0]
    expired_records[candidate_id] = (
        (expired_request.model_copy(update={"expires_at": FIXED_NOW}), expired_decision),
    )
    with pytest.raises(ValueError):
        inputs.service.validate_approvals(
            approval_records=expired_records,
            bindings=bindings,
            risk_assessments=risks,
            identities=identities,
            baseline_snapshot=baseline,
            fixture_fingerprint=inputs.fixture_fingerprint,
            overlay_fingerprints=overlay_fingerprints,
            rollback_fingerprints=rollback_fingerprints,
            overlay_expires_at=EXPIRES_AT,
        )

    duties_records = dict(inputs.approval_records)
    duties_request, duties_decision = duties_records[candidate_id][0]
    duties_records[candidate_id] = (
        (
            duties_request,
            ApprovalDecision(
                **{
                    **duties_decision.model_dump(mode="python"),
                    "decided_by": duties_request.requested_by,
                }
            ),
        ),
    )
    with pytest.raises(ValueError):
        inputs.service.validate_approvals(
            approval_records=duties_records,
            bindings=bindings,
            risk_assessments=risks,
            identities=identities,
            baseline_snapshot=baseline,
            fixture_fingerprint=inputs.fixture_fingerprint,
            overlay_fingerprints=overlay_fingerprints,
            rollback_fingerprints=rollback_fingerprints,
            overlay_expires_at=EXPIRES_AT,
        )


def test_adaptation_identity_is_deterministic_and_version_independent():
    inputs = build_synthetic_shadow_pilot_inputs()
    bindings = inputs.service.bind_candidates(
        signal_batch=inputs.signal_batch,
        candidates=inputs.candidates,
        observed_at=FIXED_NOW,
        valid_until=EXPIRES_AT,
    )
    identities = inputs.service.derive_adaptation_identities(bindings)
    repeat = inputs.service.derive_adaptation_identities(bindings)

    assert [item.identity_fingerprint for item in identities] == [
        item.identity_fingerprint for item in repeat
    ]
    assert len({item.adaptation_identity_id for item in identities}) == 9
