"""Autonomy governor tests."""

from datetime import UTC, datetime, timedelta

from aion_brain.autonomy.delegation import DelegationService
from aion_brain.autonomy.governor import AutonomyGovernor
from aion_brain.contracts.autonomy import (
    AutonomyDecisionRequest,
    AutonomyProfile,
    DelegationGrant,
)
from tests.autonomy_fakes import AllowPolicy, autonomy_repository, make_test_settings


def test_governor_allows_safe_dry_run_by_default() -> None:
    """Default v0.1 autonomy allows bounded dry-run planning."""
    governor = make_governor()

    decision = governor.decide(
        decision_request(
            requested_mode="dry_run",
            action_type="context.compile",
            risk_level="low",
        )
    )

    assert decision.allow is True
    assert decision.reason == "autonomy_allowed"
    assert decision.resolved_mode == "dry_run"


def test_governor_blocks_risk_above_default_ceiling() -> None:
    """High-risk requests fail closed with the default medium risk ceiling."""
    decision = make_governor().decide(
        decision_request(
            requested_mode="dry_run",
            action_type="capability.invoke",
            risk_level="high",
        )
    )

    assert decision.allow is False
    assert decision.reason == "risk_exceeds_autonomy_limit"


def test_governor_blocks_external_models_by_default() -> None:
    """External model access must be explicitly enabled by profile."""
    decision = make_governor().decide(
        decision_request(
            requested_mode="dry_run",
            action_type="model.complete",
            risk_level="low",
            context={"security_scope": ["workspace:main"], "uses_external_model": True},
        )
    )

    assert decision.allow is False
    assert decision.reason == "external_models_not_allowed"


def test_governor_allows_delegated_control_only_with_active_grant() -> None:
    """Delegated controlled mode requires an explicit active delegation."""
    repository = autonomy_repository()
    repository.save_profile(controlled_profile())
    repository.save_delegation(delegation_grant())
    policy = AllowPolicy()
    delegation_service = DelegationService(repository, policy)
    governor = make_governor(
        repository=repository,
        policy=policy,
        delegation_service=delegation_service,
        settings=make_test_settings(AION_AUTONOMY_DEFAULT_MAX_MODE="delegated_controlled"),
    )

    decision = governor.decide(
        decision_request(
            requested_mode="delegated_controlled",
            action_type="capability.invoke",
            resource_type="capability",
            risk_level="medium",
            context={"security_scope": ["workspace:main"]},
        )
    )

    assert decision.allow is True
    assert decision.delegation_id == "delegation-1"


def test_governor_fails_closed_when_policy_denies_autonomy_decision() -> None:
    """The governor honors the external policy boundary before resolving autonomy."""
    governor = make_governor(policy=AllowPolicy(deny_action="autonomy.decide"))

    decision = governor.decide(decision_request())

    assert decision.allow is False
    assert decision.resolved_mode == "disabled"
    assert decision.reason == "denied"


def make_governor(
    *,
    repository=None,
    policy: AllowPolicy | None = None,
    delegation_service: DelegationService | None = None,
    settings=None,
) -> AutonomyGovernor:
    """Create a governor with local fakes."""
    repo = repository or autonomy_repository()
    selected_policy = policy or AllowPolicy()
    return AutonomyGovernor(
        repo,
        selected_policy,
        delegation_service=delegation_service,
        settings=settings or make_test_settings(),
    )


def decision_request(
    *,
    requested_mode: str = "dry_run",
    action_type: str = "context.compile",
    resource_type: str = "context",
    risk_level: str = "low",
    context: dict[str, object] | None = None,
) -> AutonomyDecisionRequest:
    """Create a generic autonomy decision request."""
    return AutonomyDecisionRequest(
        trace_id="trace-1",
        actor_id="actor-1",
        workspace_id="workspace-1",
        requested_mode=requested_mode,  # type: ignore[arg-type]
        action_type=action_type,
        resource_type=resource_type,
        resource_id="resource-1",
        risk_level=risk_level,  # type: ignore[arg-type]
        approval_present=True,
        context=context or {"security_scope": ["workspace:main"]},
        metadata={},
    )


def controlled_profile() -> AutonomyProfile:
    """Create an explicitly controlled generic profile."""
    now = datetime.now(UTC)
    return AutonomyProfile(
        autonomy_profile_id="profile-1",
        name="Controlled profile",
        description="Controlled generic profile.",
        status="active",
        actor_id="actor-1",
        workspace_id="workspace-1",
        owner_scope=["workspace:main"],
        default_mode="assist",
        max_mode="delegated_controlled",
        max_risk_level="medium",
        allowed_action_types=[],
        denied_action_types=[],
        external_models_allowed=False,
        external_tools_allowed=True,
        background_workflows_allowed=False,
        scheduler_allowed=False,
        skill_promotion_allowed=False,
        memory_forgetting_allowed=False,
        approval_required_modes=["supervised_controlled", "delegated_controlled"],
        constraints=["explicit_controlled_profile"],
        metadata={},
        created_by="actor-1",
        created_at=now,
        updated_at=now,
    )


def delegation_grant() -> DelegationGrant:
    """Create an active generic delegation."""
    return DelegationGrant(
        delegation_id="delegation-1",
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
        reason="bounded generic delegation",
        created_at=datetime.now(UTC),
        expires_at=datetime.now(UTC) + timedelta(hours=1),
        revoked_at=None,
    )
