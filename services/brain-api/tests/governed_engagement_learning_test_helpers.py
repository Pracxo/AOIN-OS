from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from aion_brain.contracts.approvals import ApprovalDecision, ApprovalRequest
from aion_brain.contracts.governed_engagement_learning import engagement_fingerprint
from aion_brain.contracts.knowledge_verified_memory import (
    EngagementLearningCandidate,
    EngagementLearningCandidateBatch,
    EngagementSignalBatch,
    EngagementSignalKind,
)
from aion_brain.governed_learning_memory.engagement_application_approval import (
    REQUIRED_ACTION_TYPE,
    REQUIRED_APPROVAL_SCOPE,
    REQUIRED_RESOURCE_TYPE,
)
from aion_brain.governed_learning_memory.engagement_shadow_application import (
    ControlledEngagementShadowApplicationService,
)
from aion_brain.knowledge_intelligence.engagement_learning_candidates import (
    build_engagement_learning_candidates,
)
from aion_brain.knowledge_intelligence.engagement_signal_policy import (
    build_engagement_signal,
    build_engagement_signal_batch,
)

FIXED_NOW = datetime(2026, 1, 1, tzinfo=UTC)
EXPIRES_AT = FIXED_NOW + timedelta(minutes=30)
SHADOW_SESSION_ID = "shadow-session-aion-226-pilot"


@dataclass(frozen=True)
class EngagementShadowPilotInputs:
    service: ControlledEngagementShadowApplicationService
    signal_batch: EngagementSignalBatch
    candidate_batch: EngagementLearningCandidateBatch
    candidates: tuple[EngagementLearningCandidate, ...]
    approval_records: dict[
        str, tuple[tuple[ApprovalRequest, ApprovalDecision], ...]
    ]
    fixture_fingerprint: str
    operator_identity_fingerprint: str
    now: datetime
    expires_at: datetime


def build_synthetic_engagement_signal_batch() -> EngagementSignalBatch:
    entries = (
        (
            "signal-research-gap",
            EngagementSignalKind.QUERY_REPEATED,
            "repeated-topic",
            (),
        ),
        (
            "signal-clarification",
            EngagementSignalKind.CLARIFICATION_REQUESTED,
            "clarification-requested",
            (),
        ),
        (
            "signal-retrieval-strategy",
            EngagementSignalKind.RETRIEVAL_FAILED,
            "retrieval-failed",
            (),
        ),
        (
            "signal-source-selection",
            EngagementSignalKind.RETRIEVAL_SUCCEEDED,
            "retrieval-succeeded",
            (),
        ),
        (
            "signal-domain-routing",
            EngagementSignalKind.CORRECTION_SUBMITTED,
            "routing-correction",
            ("domain-routing",),
        ),
        (
            "signal-verification-rule",
            EngagementSignalKind.CORRECTION_SUBMITTED,
            "verification-correction",
            ("verification-rule",),
        ),
        (
            "signal-tool-manifest",
            EngagementSignalKind.CORRECTION_SUBMITTED,
            "tool-gap",
            ("tool-manifest",),
        ),
        (
            "signal-response-quality",
            EngagementSignalKind.RESPONSE_REJECTED,
            "response-rejected",
            (),
        ),
        (
            "signal-preference",
            EngagementSignalKind.RESPONSE_ACCEPTED,
            "response-accepted",
            ("preference",),
        ),
    )
    signals = tuple(
        build_engagement_signal(
            signal_id=signal_id,
            signal_kind=signal_kind,
            session_fingerprint=engagement_fingerprint({"session": signal_id}),
            response_fingerprint=engagement_fingerprint({"response": signal_id}),
            subject_fingerprint=engagement_fingerprint({"subject": signal_id}),
            bounded_outcome_code=outcome_code,
            metadata_codes=metadata_codes,
            occurred_at=FIXED_NOW,
        )
        for signal_id, signal_kind, outcome_code, metadata_codes in entries
    )
    return build_engagement_signal_batch(
        batch_id="engagement-shadow-batch",
        signals=signals,
    )


def build_synthetic_engagement_candidates(
    signal_batch: EngagementSignalBatch,
) -> EngagementLearningCandidateBatch:
    return build_engagement_learning_candidates(
        batch_id="engagement-shadow-candidates",
        signal_batch=signal_batch,
        created_at=FIXED_NOW,
    )


def build_approval_records(
    *,
    service: ControlledEngagementShadowApplicationService,
    signal_batch: EngagementSignalBatch,
    candidates: tuple[EngagementLearningCandidate, ...],
    fixture_fingerprint: str,
) -> dict[str, tuple[tuple[ApprovalRequest, ApprovalDecision], ...]]:
    bindings = service.bind_candidates(
        signal_batch=signal_batch,
        candidates=candidates,
        observed_at=FIXED_NOW,
        valid_until=EXPIRES_AT,
    )
    risks = service.classify_risk(bindings, assessed_at=FIXED_NOW)
    identities = service.derive_adaptation_identities(bindings)
    baseline = service.build_baseline_snapshot(
        bindings=bindings,
        fixture_fingerprint=fixture_fingerprint,
        captured_at=FIXED_NOW,
    )
    overlay_fingerprints = {
        binding.learning_candidate_id: engagement_fingerprint(
            {
                "candidate": binding.candidate_fingerprint,
                "baseline": baseline.snapshot_fingerprint,
                "fixture": fixture_fingerprint,
            }
        )
        for binding in bindings
    }
    rollback_fingerprints = {
        binding.learning_candidate_id: engagement_fingerprint(
            {
                "rollback": binding.candidate_fingerprint,
                "fixture": fixture_fingerprint,
            }
        )
        for binding in bindings
    }
    risk_by_candidate = {risk.candidate_id: risk for risk in risks}
    identity_by_candidate = {identity.candidate_id: identity for identity in identities}
    records: dict[str, tuple[tuple[ApprovalRequest, ApprovalDecision], ...]] = {}
    for binding in bindings:
        risk = risk_by_candidate[binding.learning_candidate_id]
        identity = identity_by_candidate[binding.learning_candidate_id]
        pairs: list[tuple[ApprovalRequest, ApprovalDecision]] = []
        for index in range(risk.required_independent_approvers):
            request_id = f"approval-request-{binding.learning_candidate_id}-{index + 1}"
            payload = {
                "candidate_id": binding.learning_candidate_id,
                "candidate_fingerprint": binding.candidate_fingerprint,
                "candidate_version": binding.candidate_version,
                "signal_fingerprints": binding.signal_fingerprints,
                "adaptation_identity_id": identity.adaptation_identity_id,
                "adaptation_version": 1,
                "target_component_code": binding.target_component_code,
                "target_policy_code": binding.target_policy_code,
                "overlay_fingerprint": overlay_fingerprints[binding.learning_candidate_id],
                "baseline_snapshot_fingerprint": baseline.snapshot_fingerprint,
                "fixture_fingerprint": fixture_fingerprint,
                "rollback_plan_fingerprint": rollback_fingerprints[
                    binding.learning_candidate_id
                ],
                "overlay_expires_at": EXPIRES_AT.isoformat(),
            }
            request = ApprovalRequest(
                approval_request_id=request_id,
                actor_id=f"requester-{index + 1}",
                requested_by=f"requester-{binding.learning_candidate_id}-{index + 1}",
                action_type=REQUIRED_ACTION_TYPE,
                resource_type=REQUIRED_RESOURCE_TYPE,
                resource_id=binding.learning_candidate_id,
                title="Engagement shadow approval",
                description="Approve bounded non-factual shadow overlay",
                status="approved",
                priority="normal",
                approval_scope=[REQUIRED_APPROVAL_SCOPE],
                payload=payload,
                expires_at=EXPIRES_AT,
                created_at=FIXED_NOW,
            )
            decision = ApprovalDecision(
                approval_decision_id=(
                    f"approval-decision-{binding.learning_candidate_id}-{index + 1}"
                ),
                approval_request_id=request_id,
                decided_by=f"approver-{binding.learning_candidate_id}-{index + 1}",
                decision="approve",
                reason="Approve bounded shadow overlay",
                created_at=FIXED_NOW,
            )
            pairs.append((request, decision))
        records[binding.learning_candidate_id] = tuple(pairs)
    return records


def build_synthetic_shadow_pilot_inputs() -> EngagementShadowPilotInputs:
    service = ControlledEngagementShadowApplicationService()
    signal_batch = build_synthetic_engagement_signal_batch()
    candidate_batch = build_synthetic_engagement_candidates(signal_batch)
    fixture_fingerprint = engagement_fingerprint({"fixture": "synthetic-shadow"})
    return EngagementShadowPilotInputs(
        service=service,
        signal_batch=signal_batch,
        candidate_batch=candidate_batch,
        candidates=candidate_batch.candidates,
        approval_records=build_approval_records(
            service=service,
            signal_batch=signal_batch,
            candidates=candidate_batch.candidates,
            fixture_fingerprint=fixture_fingerprint,
        ),
        fixture_fingerprint=fixture_fingerprint,
        operator_identity_fingerprint=engagement_fingerprint(
            {"operator": "operator-reviewer"}
        ),
        now=FIXED_NOW,
        expires_at=EXPIRES_AT,
    )
