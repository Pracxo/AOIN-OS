from __future__ import annotations

import pytest
from governed_engagement_learning_test_helpers import (
    EXPIRES_AT,
    FIXED_NOW,
    build_synthetic_shadow_pilot_inputs,
)

from aion_brain.contracts.governed_engagement_learning import (
    EngagementApplicationRiskClass,
    EngagementCandidateDisposition,
    engagement_fingerprint,
    target_spec_for_candidate_kind,
)
from aion_brain.contracts.knowledge_verified_memory import (
    EngagementLearningCandidate,
    EngagementLearningLifecycleStatus,
    verified_knowledge_fingerprint,
)
from aion_brain.governed_learning_memory.engagement_candidate_binding import (
    bind_engagement_candidate,
    build_lifecycle_evidence,
)


def _candidate_variant(candidate: EngagementLearningCandidate, **updates):
    payload = candidate.model_dump(mode="python", exclude={"candidate_fingerprint"})
    payload.update(updates)
    return EngagementLearningCandidate.model_validate(
        {**payload, "candidate_fingerprint": verified_knowledge_fingerprint(payload)}
    )


def test_candidate_binding_preserves_exact_lineage_and_target_registry():
    inputs = build_synthetic_shadow_pilot_inputs()
    bindings = inputs.service.bind_candidates(
        signal_batch=inputs.signal_batch,
        candidates=inputs.candidates,
        observed_at=FIXED_NOW,
        valid_until=EXPIRES_AT,
    )

    assert len(bindings) == 9
    assert {binding.candidate_kind for binding in bindings} == {
        candidate.candidate_kind for candidate in inputs.candidates
    }
    for binding in bindings:
        spec = target_spec_for_candidate_kind(binding.candidate_kind)
        assert binding.signal_ids == binding.candidate.signal_ids
        assert binding.signal_fingerprints == binding.candidate.signal_fingerprints
        assert binding.target_component_code == spec.target_component_code
        assert binding.target_policy_code == spec.target_policy_code
        assert binding.candidate_disposition is EngagementCandidateDisposition.ELIGIBLE_FOR_SHADOW
        assert binding.non_factual_invariant_passed is True
        assert binding.zero_confidence_effect_passed is True
        assert binding.zero_knowledge_effect_passed is True
        assert binding.zero_source_independence_effect_passed is True
        assert binding.zero_belief_effect_passed is True


def test_engagement_risk_classification_is_deterministic():
    inputs = build_synthetic_shadow_pilot_inputs()
    bindings = inputs.service.bind_candidates(
        signal_batch=inputs.signal_batch,
        candidates=inputs.candidates,
        observed_at=FIXED_NOW,
        valid_until=EXPIRES_AT,
    )
    risks = inputs.service.classify_risk(bindings, assessed_at=FIXED_NOW)

    assert [risk.assessment_fingerprint for risk in risks] == [
        risk.assessment_fingerprint
        for risk in inputs.service.classify_risk(bindings, assessed_at=FIXED_NOW)
    ]
    assert sum(risk.risk_class is EngagementApplicationRiskClass.LOW for risk in risks) == 4
    assert sum(
        risk.risk_class is EngagementApplicationRiskClass.ELEVATED for risk in risks
    ) == 5
    assert {risk.required_independent_approvers for risk in risks} == {1, 2}


def test_lifecycle_expiry_rejection_supersession_and_retraction_block_application():
    inputs = build_synthetic_shadow_pilot_inputs()
    candidate = inputs.candidates[0]
    variants = (
        _candidate_variant(candidate, expires_at=FIXED_NOW),
        _candidate_variant(
            candidate,
            lifecycle_status=EngagementLearningLifecycleStatus.OPERATOR_REVIEW_REJECTED,
        ),
        _candidate_variant(
            candidate,
            lifecycle_status=EngagementLearningLifecycleStatus.SUPERSEDED,
        ),
    )

    for variant in variants:
        bindings = inputs.service.bind_candidates(
            signal_batch=inputs.signal_batch,
            candidates=(variant,),
            observed_at=FIXED_NOW,
            valid_until=EXPIRES_AT,
        )
        assert bindings[0].candidate_disposition is not (
            EngagementCandidateDisposition.ELIGIBLE_FOR_SHADOW
        )
        with pytest.raises(ValueError):
            inputs.service.validate_candidate_lifecycle(bindings)

    retracted = bind_engagement_candidate(
        binding_id=f"binding-{candidate.learning_candidate_id}-retracted",
        candidate=candidate,
        signal_batch=inputs.signal_batch,
        lifecycle_evidence=build_lifecycle_evidence(
            lifecycle_evidence_id=f"lifecycle-{candidate.learning_candidate_id}-retracted",
            candidate=candidate,
            observed_at=FIXED_NOW,
            valid_until=EXPIRES_AT,
            retraction_record_fingerprint=engagement_fingerprint(
                {"retraction": candidate.learning_candidate_id}
            ),
        ),
    )
    assert retracted.candidate_disposition is EngagementCandidateDisposition.RETRACTED
    with pytest.raises(ValueError):
        inputs.service.validate_candidate_lifecycle((retracted,))
