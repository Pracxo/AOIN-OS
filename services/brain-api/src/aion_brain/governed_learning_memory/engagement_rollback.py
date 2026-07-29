"""Rollback and expiry planning for engagement shadow sessions."""

from __future__ import annotations

from aion_brain.contracts.governed_engagement_learning import (
    EngagementBaselineSnapshot,
    EngagementOverlaySnapshot,
    EngagementRollbackPlan,
    EngagementRollbackStep,
    build_record,
)


def build_engagement_rollback_plan(
    *,
    rollback_plan_id: str,
    shadow_session_id: str,
    overlay_snapshot: EngagementOverlaySnapshot,
    baseline_snapshot: EngagementBaselineSnapshot,
) -> EngagementRollbackPlan:
    """Build deterministic no-persistence rollback steps for a shadow session."""

    operations = (
        "remove_overlay_from_shadow_session",
        "restore_baseline_snapshot",
        "invalidate_overlay_snapshot",
        "expire_adaptation_version",
        "preserve_evaluation_evidence",
        "create_operator_review_item",
        "retain_baseline",
    )
    steps = tuple(
        build_record(
            EngagementRollbackStep,
            {
                "rollback_step_id": f"{rollback_plan_id}-step-{index:02d}",
                "operation": operation,
                "target_reference_id": overlay_snapshot.overlay_snapshot_id
                if index != 2
                else baseline_snapshot.baseline_snapshot_id,
                "order": index,
                "persistent_write_applied": False,
                "production_policy_effect": False,
                "runtime_effect": False,
            },
            "step_fingerprint",
        )
        for index, operation in enumerate(operations, start=1)
    )
    payload = {
        "schema_version": "aion-glm-engagement-rollback/v1",
        "rollback_plan_id": rollback_plan_id,
        "shadow_session_id": shadow_session_id,
        "overlay_snapshot_fingerprint": overlay_snapshot.snapshot_fingerprint,
        "baseline_snapshot_fingerprint": baseline_snapshot.snapshot_fingerprint,
        "steps": steps,
        "step_count": len(steps),
        "reason_codes": ("engagement_rollback_valid", "engagement_expiry_valid"),
        "read_only": True,
        "redacted": True,
        "persistent_write_applied": False,
        "production_policy_effect": False,
        "runtime_effect": False,
    }
    return build_record(EngagementRollbackPlan, payload, "rollback_plan_fingerprint")


__all__ = ["build_engagement_rollback_plan"]
