"""Deactivation decision service for disabled shadow activation."""

from __future__ import annotations

from datetime import datetime

from aion_brain.contracts.self_improvement_shadow_activation import (
    ShadowActivationCandidate,
    ShadowActivationDeactivationDecision,
    ShadowActivationDeactivationPlan,
    ShadowActivationIncidentRecord,
    ShadowActivationMonitoringDecision,
    ShadowActivationRequest,
    evaluate_shadow_activation_deactivation,
)


class ShadowActivationDeactivationService:
    """Build advisory deactivation evidence without managing any runtime process."""

    def evaluate(
        self,
        *,
        candidate: ShadowActivationCandidate,
        request: ShadowActivationRequest,
        monitoring_decision: ShadowActivationMonitoringDecision,
        deactivation_plan: ShadowActivationDeactivationPlan,
        now: datetime,
    ) -> tuple[ShadowActivationDeactivationDecision, ShadowActivationIncidentRecord | None]:
        """Return an advisory decision and optional redacted incident record."""

        decision = evaluate_shadow_activation_deactivation(
            health_decision=monitoring_decision,
            deactivation_plan=deactivation_plan,
            now=now,
            decision_id=f"{request.activation_request_id}-deactivation",
        )
        incident = None
        if decision.triggered:
            incident = ShadowActivationIncidentRecord(
                incident_id=f"{request.activation_request_id}-incident",
                activation_candidate_id=candidate.activation_candidate_id,
                activation_request_id=request.activation_request_id,
                incident_type="activation_deactivation_required",
                trigger_codes=decision.triggers,
                monitoring_snapshot_fingerprint=monitoring_decision.fingerprint,
                deactivation_plan_fingerprint=deactivation_plan.fingerprint,
                created_at=now,
            )
        return decision, incident


__all__ = [
    "ShadowActivationCandidate",
    "ShadowActivationDeactivationDecision",
    "ShadowActivationDeactivationPlan",
    "ShadowActivationDeactivationService",
    "ShadowActivationIncidentRecord",
    "ShadowActivationMonitoringDecision",
    "ShadowActivationRequest",
    "evaluate_shadow_activation_deactivation",
]
