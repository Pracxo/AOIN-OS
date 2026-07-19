"""Disabled-by-default canary controller for AION-174 self-improvement."""

from __future__ import annotations

from aion_brain.self_improvement.canary_contracts import (
    CanaryApprovalBinding,
    CanaryDecision,
    CanaryObservation,
    CanaryPlan,
    RollbackDecision,
)
from aion_brain.self_improvement.monitoring import CanaryMonitor, CanaryMonitoringSummary
from aion_brain.self_improvement.rollback_controller import RollbackController


class CanaryController:
    """Run local canary simulations without production activation."""

    def __init__(
        self,
        monitor: CanaryMonitor | None = None,
        rollback_controller: RollbackController | None = None,
    ) -> None:
        self._monitor = monitor or CanaryMonitor()
        self._rollback_controller = rollback_controller or RollbackController()

    def approve(self, plan: CanaryPlan, approval: CanaryApprovalBinding) -> CanaryPlan:
        """Move a plan to approved only when approval evidence matches exactly."""

        _require_valid_approval(plan, approval)
        return plan.model_copy(update={"state": "approved"})

    def start_local_simulation(
        self,
        plan: CanaryPlan,
        approval: CanaryApprovalBinding,
    ) -> CanaryDecision:
        """Start a disabled local simulation, not production canary runtime."""

        _require_valid_approval(plan, approval)
        if plan.state != "approved":
            return CanaryDecision(
                plan_id=plan.plan_id,
                from_state=plan.state,
                to_state=plan.state,
                allowed=False,
                reason_codes=("canary_plan_not_approved",),
            )
        if plan.canary_runtime_enabled or plan.production_exposure_enabled:
            return CanaryDecision(
                plan_id=plan.plan_id,
                from_state=plan.state,
                to_state=plan.state,
                allowed=False,
                reason_codes=("production_canary_runtime_disabled",),
            )
        return CanaryDecision(
            plan_id=plan.plan_id,
            from_state=plan.state,
            to_state="running",
            allowed=True,
            reason_codes=("disabled_local_canary_simulation_started",),
        )

    def evaluate(self, plan: CanaryPlan, summary: CanaryMonitoringSummary) -> CanaryDecision:
        """Evaluate a running canary as passed or failed from monitoring evidence."""

        if plan.state != "running":
            return CanaryDecision(
                plan_id=plan.plan_id,
                from_state=plan.state,
                to_state=plan.state,
                allowed=False,
                reason_codes=("canary_not_running",),
            )
        if summary.healthy:
            return CanaryDecision(
                plan_id=plan.plan_id,
                from_state="running",
                to_state="passed",
                allowed=True,
                reason_codes=("canary_metrics_healthy",),
            )
        return CanaryDecision(
            plan_id=plan.plan_id,
            from_state="running",
            to_state="failed",
            allowed=True,
            reason_codes=summary.reason_codes,
        )

    def decide_rollback(
        self,
        plan: CanaryPlan,
        summary: CanaryMonitoringSummary,
    ) -> RollbackDecision:
        """Return an automatic rollback decision for an approved local canary."""

        return self._rollback_controller.decide(
            plan,
            summary,
            approved_canary_running=plan.state == "running",
        )

    def monitor(
        self,
        plan: CanaryPlan,
        observations: tuple[CanaryObservation, ...],
    ) -> CanaryMonitoringSummary:
        """Delegate monitoring for integration tests."""

        return self._monitor.summarize(plan, observations)

    def promote(self, plan: CanaryPlan, approval: CanaryApprovalBinding) -> CanaryDecision:
        """Promote only a passed plan with still-valid approval."""

        _require_valid_approval(plan, approval)
        if plan.state != "passed":
            return CanaryDecision(
                plan_id=plan.plan_id,
                from_state=plan.state,
                to_state=plan.state,
                allowed=False,
                reason_codes=("canary_must_pass_before_promotion",),
            )
        return CanaryDecision(
            plan_id=plan.plan_id,
            from_state="passed",
            to_state="promoted",
            allowed=True,
            reason_codes=("approval_bound_canary_promoted",),
        )


def _require_valid_approval(plan: CanaryPlan, approval: CanaryApprovalBinding) -> None:
    if not approval.is_valid:
        raise ValueError("valid exact canary approval is required")
    if approval.plan_id != plan.plan_id:
        raise ValueError("canary approval must match the plan")


__all__ = ["CanaryController"]
