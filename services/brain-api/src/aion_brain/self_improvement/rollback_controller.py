"""Rollback controller for approved canary simulations."""

from __future__ import annotations

from aion_brain.self_improvement.canary_contracts import (
    CanaryPlan,
    RollbackDecision,
)
from aion_brain.self_improvement.monitoring import CanaryMonitoringSummary


class RollbackController:
    """Decide rollback only inside an already approved canary plan."""

    def decide(
        self,
        plan: CanaryPlan,
        summary: CanaryMonitoringSummary,
        *,
        approved_canary_running: bool,
    ) -> RollbackDecision:
        """Return rollback decision without performing runtime mutation."""

        if plan.state != "running":
            return RollbackDecision(
                plan_id=plan.plan_id,
                rollback_required=False,
                rollback_allowed=False,
                rollback_commit_sha=plan.rollback_commit_sha,
                reason_codes=("canary_not_running",),
            )
        if summary.plan_id != plan.plan_id:
            return RollbackDecision(
                plan_id=plan.plan_id,
                rollback_required=True,
                rollback_allowed=False,
                rollback_commit_sha=plan.rollback_commit_sha,
                triggers=("unexpected_runtime_effect",),
                reason_codes=("monitoring_plan_mismatch",),
            )
        if not summary.rollback_triggers:
            return RollbackDecision(
                plan_id=plan.plan_id,
                rollback_required=False,
                rollback_allowed=False,
                rollback_commit_sha=plan.rollback_commit_sha,
                reason_codes=("rollback_not_required",),
            )
        if not approved_canary_running:
            return RollbackDecision(
                plan_id=plan.plan_id,
                rollback_required=True,
                rollback_allowed=False,
                rollback_commit_sha=plan.rollback_commit_sha,
                triggers=summary.rollback_triggers,
                reason_codes=("approved_canary_required_for_automatic_rollback",),
            )
        return RollbackDecision(
            plan_id=plan.plan_id,
            rollback_required=True,
            rollback_allowed=True,
            rollback_commit_sha=plan.rollback_commit_sha,
            triggers=summary.rollback_triggers,
            reason_codes=("approved_threshold_rollback",),
        )


__all__ = ["RollbackController"]
