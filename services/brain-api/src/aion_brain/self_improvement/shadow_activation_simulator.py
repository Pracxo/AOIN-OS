"""Simulation-only disabled shadow activation control plane."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, field_validator, model_validator

from aion_brain.contracts.self_improvement_shadow_activation import (
    FROZEN_MODEL_CONFIG,
    SHADOW_ACTIVATION_SIMULATION_SCHEMA_VERSION,
    ShadowActivationApprovalBinding,
    ShadowActivationApprovalValidation,
    ShadowActivationBudgetDecision,
    ShadowActivationCandidate,
    ShadowActivationCurrentFacts,
    ShadowActivationDeactivationDecision,
    ShadowActivationHealthSnapshot,
    ShadowActivationIncidentRecord,
    ShadowActivationMonitoringDecision,
    ShadowActivationOperatorReviewItem,
    ShadowActivationRequest,
    ShadowActivationResourceUsage,
    ShadowActivationStateRecord,
    evaluate_shadow_activation_budget,
    fingerprint_activation_model,
    require_activation_identifier,
    require_utc_datetime,
    validate_activation_candidate,
    validate_shadow_activation_approval,
)
from aion_brain.self_improvement.shadow_activation import (
    transition_shadow_activation_state,
)
from aion_brain.self_improvement.shadow_activation_deactivation import (
    ShadowActivationDeactivationService,
)
from aion_brain.self_improvement.shadow_activation_monitoring import evaluate_monitoring_snapshot


class ShadowActivationSimulationRequest(BaseModel):
    """Synthetic or redacted request for simulation-only evaluation."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: str = SHADOW_ACTIVATION_SIMULATION_SCHEMA_VERSION
    simulation_id: str = Field(min_length=1, max_length=128)
    candidate: ShadowActivationCandidate
    request: ShadowActivationRequest
    approval_binding: ShadowActivationApprovalBinding
    current_facts: ShadowActivationCurrentFacts
    resource_usage: ShadowActivationResourceUsage
    health_snapshots: tuple[ShadowActivationHealthSnapshot, ...]
    created_at: datetime
    simulation_only: bool = True
    shadow_activation_enabled: bool = False
    runtime_effect: bool = False
    fingerprint: str = ""

    @field_validator("simulation_id")
    @classmethod
    def simulation_id_is_safe(cls, value: str) -> str:
        return require_activation_identifier(value, "simulation_id")

    @field_validator("created_at")
    @classmethod
    def created_at_is_utc(cls, value: datetime) -> datetime:
        return require_utc_datetime(value)

    @model_validator(mode="after")
    def request_is_simulation_only(self) -> ShadowActivationSimulationRequest:
        if not self.simulation_only or self.shadow_activation_enabled or self.runtime_effect:
            raise ValueError("activation simulation request cannot enable runtime effects")
        if (
            self.request.activation_candidate.activation_candidate_id
            != self.candidate.activation_candidate_id
        ):
            raise ValueError("activation simulation request candidate mismatch")
        if not self.fingerprint:
            object.__setattr__(self, "fingerprint", fingerprint_activation_model(self))
        return self


class ShadowActivationSimulationResult(BaseModel):
    """Simulation-only result with no runtime side effects."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: str = SHADOW_ACTIVATION_SIMULATION_SCHEMA_VERSION
    simulation_id: str
    candidate_id: str
    state_sequence: tuple[str, ...]
    decision_outcomes: tuple[str, ...]
    approval_validation: ShadowActivationApprovalValidation
    budget_decision: ShadowActivationBudgetDecision
    monitoring_decisions: tuple[ShadowActivationMonitoringDecision, ...]
    deactivation_decision: ShadowActivationDeactivationDecision
    incident_records: tuple[ShadowActivationIncidentRecord, ...]
    operator_review_item: ShadowActivationOperatorReviewItem
    simulation_passed: bool
    shadow_activation_enabled: bool = False
    runtime_effect: bool = False
    source_modified: bool = False
    git_mutated: bool = False
    pull_request_created: bool = False
    approval_created: bool = False
    merged: bool = False
    active_learning_promoted: bool = False
    production_exposure: bool = False
    created_at: datetime
    fingerprint: str = ""

    @field_validator("simulation_id", "candidate_id")
    @classmethod
    def identifiers_are_safe(cls, value: str, info: object) -> str:
        field_name = getattr(info, "field_name", "identifier")
        return require_activation_identifier(value, field_name)

    @field_validator("created_at")
    @classmethod
    def created_at_is_utc(cls, value: datetime) -> datetime:
        return require_utc_datetime(value)

    @model_validator(mode="after")
    def result_is_disabled(self) -> ShadowActivationSimulationResult:
        if "active" in self.state_sequence:
            raise ValueError("activation simulation cannot enter active state")
        if any(
            (
                self.shadow_activation_enabled,
                self.runtime_effect,
                self.source_modified,
                self.git_mutated,
                self.pull_request_created,
                self.approval_created,
                self.merged,
                self.active_learning_promoted,
                self.production_exposure,
            )
        ):
            raise ValueError("activation simulation cannot create side effects")
        if not self.fingerprint:
            object.__setattr__(self, "fingerprint", fingerprint_activation_model(self))
        return self


class ControlledShadowActivationSimulator:
    """Run in-memory simulations of the disabled activation control plane."""

    def simulate(
        self,
        simulation_request: ShadowActivationSimulationRequest,
    ) -> ShadowActivationSimulationResult:
        """Simulate activation-control decisions without persistent mutation."""

        now = simulation_request.created_at
        candidate = simulation_request.candidate
        request = simulation_request.request
        validate_activation_candidate(candidate, now=now)
        state = _initial_state(candidate.activation_candidate_id, now)
        states = [state.current_state]
        outcomes: list[str] = ["candidate_valid"]
        for next_state, reason in (
            ("evidence_ready", "candidate_evidence_valid"),
            ("approval_pending", "approval_required"),
        ):
            state = transition_shadow_activation_state(
                state,
                next_state,
                actor_principal_id=request.requesting_operator_principal_id,
                reason_code=reason,  # type: ignore[arg-type]
                transitioned_at=now,
                state_record_id=f"{simulation_request.simulation_id}-{next_state}",
            )
            states.append(state.current_state)
        approval_validation = validate_shadow_activation_approval(
            approval=simulation_request.approval_binding,
            candidate=candidate,
            request=request,
            current_facts=simulation_request.current_facts,
            now=now,
        )
        budget_decision = evaluate_shadow_activation_budget(
            simulation_request.resource_usage,
            request.resource_budget,
        )
        monitoring_decisions = tuple(
            evaluate_monitoring_snapshot(
                snapshot,
                request.monitoring_plan,
                activation_window_end=request.activation_window_end,
                maximum_runs=request.maximum_runs,
                now=now,
            )
            for snapshot in simulation_request.health_snapshots
        )
        service = ShadowActivationDeactivationService()
        last_monitoring = (
            monitoring_decisions[-1] if monitoring_decisions else _passing_monitoring(now)
        )
        deactivation_decision, incident = service.evaluate(
            candidate=candidate,
            request=request,
            monitoring_decision=last_monitoring,
            deactivation_plan=request.deactivation_plan,
            now=now,
        )
        incidents = (incident,) if incident else ()
        if not approval_validation.valid:
            outcomes.append("approval_invalid")
            simulation_passed = False
        else:
            for next_state, reason in (
                ("approved_disabled", "approval_valid"),
                ("simulation_ready", "simulation_ready"),
            ):
                state = transition_shadow_activation_state(
                    state,
                    next_state,
                    actor_principal_id=request.requesting_operator_principal_id,
                    reason_code=reason,  # type: ignore[arg-type]
                    transitioned_at=now,
                    state_record_id=f"{simulation_request.simulation_id}-{next_state}",
                )
                states.append(state.current_state)
            if deactivation_decision.triggered or not budget_decision.within_budget:
                outcomes.append("simulation_failed")
                simulation_passed = False
            else:
                for next_state, reason in (
                    ("simulated", "simulation_passed"),
                    ("review_pending", "operator_review_required"),
                ):
                    state = transition_shadow_activation_state(
                        state,
                        next_state,
                        actor_principal_id=request.requesting_operator_principal_id,
                        reason_code=reason,  # type: ignore[arg-type]
                        transitioned_at=now,
                        state_record_id=f"{simulation_request.simulation_id}-{next_state}",
                    )
                    states.append(state.current_state)
                outcomes.append("simulation_passed")
                simulation_passed = True
        review_item = ShadowActivationOperatorReviewItem(
            review_item_id=f"{simulation_request.simulation_id}-review",
            activation_candidate_id=candidate.activation_candidate_id,
            activation_request_id=request.activation_request_id,
            current_state=states[-1],
            decision_outcome=outcomes[-1],  # type: ignore[arg-type]
            candidate_validation_summary="candidate valid",
            approval_validation_summary=(
                "approval valid" if approval_validation.valid else "approval invalid"
            ),
            budget_summary=(
                "budget satisfied" if budget_decision.within_budget else "budget exceeded"
            ),
            monitoring_summary=(
                "monitoring passed"
                if not deactivation_decision.triggered
                else "monitoring breached"
            ),
            deactivation_summary=(
                "deactivation not required"
                if not deactivation_decision.triggered
                else "deactivation required"
            ),
            evidence_fingerprints={
                "candidate": candidate.fingerprint,
                "request": request.fingerprint,
                "budget": budget_decision.fingerprint,
                "deactivation": deactivation_decision.fingerprint,
            },
            reason_codes=(
                "activation_simulation_passed",
                "activation_runtime_disabled",
                "activation_actual_activation_unauthorized",
            )
            if simulation_passed
            else (
                "activation_simulation_failed",
                "activation_runtime_disabled",
                "activation_actual_activation_unauthorized",
            ),
            created_at=now,
            expires_at=candidate.expires_at,
        )
        return ShadowActivationSimulationResult(
            simulation_id=simulation_request.simulation_id,
            candidate_id=candidate.activation_candidate_id,
            state_sequence=tuple(states),
            decision_outcomes=tuple(outcomes),
            approval_validation=approval_validation,
            budget_decision=budget_decision,
            monitoring_decisions=monitoring_decisions,
            deactivation_decision=deactivation_decision,
            incident_records=incidents,
            operator_review_item=review_item,
            simulation_passed=simulation_passed,
            created_at=now,
        )


def _initial_state(candidate_id: str, now: datetime) -> ShadowActivationStateRecord:
    return ShadowActivationStateRecord(
        state_record_id=f"{candidate_id}-state-0",
        activation_candidate_id=candidate_id,
        current_state="drafted",
        sequence_number=0,
        reason_code="runtime_disabled",
        actor_principal_id="operator-shadow-reviewer",
        transitioned_at=now,
    )


def _passing_monitoring(now: datetime) -> ShadowActivationMonitoringDecision:
    return ShadowActivationMonitoringDecision(
        monitoring_passed=True,
        deactivation_required=False,
        forbidden_counter_violation=False,
        window_expired=False,
        run_count_exhausted=False,
        kill_switch_asserted=False,
        decided_at=now,
    )


__all__ = [
    "ControlledShadowActivationSimulator",
    "ShadowActivationSimulationRequest",
    "ShadowActivationSimulationResult",
]
