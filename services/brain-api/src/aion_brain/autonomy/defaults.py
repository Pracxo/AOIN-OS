"""Default autonomy envelopes."""

from datetime import UTC, datetime
from typing import cast

from aion_brain.config import Settings
from aion_brain.contracts.autonomy import (
    AutonomyMode,
    AutonomyProfile,
    AutonomyRiskLevel,
)


def default_dev_profile(
    settings: Settings,
    *,
    actor_id: str | None,
    workspace_id: str | None,
    owner_scope: list[str],
) -> AutonomyProfile:
    """Return the conservative default autonomy profile."""
    now = datetime.now(UTC)
    return AutonomyProfile(
        autonomy_profile_id="autonomy-profile-default-dev",
        name="Default conservative autonomy profile",
        description="Default AION v0.1 autonomy envelope with no full autonomy.",
        status="active",
        actor_id=actor_id,
        workspace_id=workspace_id,
        owner_scope=owner_scope or ["workspace:main"],
        default_mode=cast(AutonomyMode, settings.autonomy_default_mode),
        max_mode=cast(AutonomyMode, settings.autonomy_default_max_mode),
        max_risk_level=cast(AutonomyRiskLevel, settings.autonomy_default_max_risk_level),
        allowed_action_types=[],
        denied_action_types=[],
        external_models_allowed=settings.autonomy_external_models_allowed_default,
        external_tools_allowed=settings.autonomy_external_tools_allowed_default,
        background_workflows_allowed=settings.autonomy_background_workflows_allowed_default,
        scheduler_allowed=settings.autonomy_scheduler_allowed_default,
        skill_promotion_allowed=settings.autonomy_skill_promotion_allowed_default,
        memory_forgetting_allowed=settings.autonomy_memory_forgetting_allowed_default,
        approval_required_modes=["supervised_controlled", "delegated_controlled"],
        constraints=["no_full_autonomy_by_default"],
        metadata={"default": True},
        created_by="aion-system",
        created_at=now,
        updated_at=now,
        disabled_at=None,
    )
