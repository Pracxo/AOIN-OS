"""Autonomy repository tests."""

from datetime import UTC, datetime, timedelta

from aion_brain.contracts.autonomy import AutonomyProfile, DelegationGrant, RunLevelRecord
from tests.autonomy_fakes import autonomy_repository


def test_repository_persists_profiles_run_levels_and_delegations() -> None:
    """AutonomyRepository stores and returns the governor-owned records."""
    repository = autonomy_repository()
    profile = repository.save_profile(profile_record("profile-1"))
    run_level = repository.save_run_level(run_level_record("run-level-1"))
    delegation = repository.save_delegation(delegation_record("delegation-1"))

    assert repository.get_profile(profile.autonomy_profile_id) == profile
    assert repository.get_active_profile(actor_id="actor-1", workspace_id="workspace-1") == profile
    assert (
        repository.get_active_run_level(actor_id="actor-1", workspace_id="workspace-1")
        == run_level
    )
    assert repository.get_delegation(delegation.delegation_id) == delegation


def test_repository_ignores_expired_active_run_level() -> None:
    """Expired run-level records are not returned as active."""
    repository = autonomy_repository()
    repository.save_run_level(
        run_level_record(
            "run-level-expired",
            expires_at=datetime.now(UTC) - timedelta(seconds=1),
        )
    )

    assert repository.get_active_run_level(actor_id="actor-1", workspace_id="workspace-1") is None


def profile_record(profile_id: str) -> AutonomyProfile:
    """Create a generic autonomy profile."""
    return AutonomyProfile(
        autonomy_profile_id=profile_id,
        name="Generic profile",
        description="Generic profile description.",
        status="active",
        actor_id="actor-1",
        workspace_id="workspace-1",
        owner_scope=["workspace:main"],
        default_mode="assist",
        max_mode="dry_run",
        max_risk_level="medium",
        allowed_action_types=[],
        denied_action_types=[],
        external_models_allowed=False,
        external_tools_allowed=False,
        background_workflows_allowed=False,
        scheduler_allowed=False,
        skill_promotion_allowed=False,
        memory_forgetting_allowed=False,
        approval_required_modes=["supervised_controlled", "delegated_controlled"],
        constraints=[],
        metadata={},
        created_by="actor-1",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


def run_level_record(
    run_level_id: str,
    *,
    expires_at: datetime | None = None,
) -> RunLevelRecord:
    """Create a generic run-level record."""
    return RunLevelRecord(
        run_level_id=run_level_id,
        actor_id="actor-1",
        workspace_id="workspace-1",
        active_profile_id=None,
        run_level="observe",
        status="active",
        reason="generic override",
        constraints=[],
        metadata={},
        set_by="actor-1",
        created_at=datetime.now(UTC),
        expires_at=expires_at,
        ended_at=None,
    )


def delegation_record(delegation_id: str) -> DelegationGrant:
    """Create a generic delegation grant."""
    return DelegationGrant(
        delegation_id=delegation_id,
        actor_id="actor-1",
        workspace_id="workspace-1",
        delegated_by="actor-1",
        delegated_to="aion-system",
        owner_scope=["workspace:main"],
        mode="delegated_controlled",
        max_risk_level="medium",
        allowed_action_types=["capability.invoke"],
        resource_types=["capability"],
        constraints=[],
        status="active",
        reason="bounded delegation",
        created_at=datetime.now(UTC),
        expires_at=datetime.now(UTC) + timedelta(hours=1),
        revoked_at=None,
    )
