"""Delegation service tests."""

from datetime import UTC, datetime, timedelta

from aion_brain.autonomy.delegation import DelegationService
from aion_brain.contracts.autonomy import DelegationGrantRequest
from tests.autonomy_fakes import AllowPolicy, autonomy_repository


def test_delegation_service_creates_and_matches_active_grant() -> None:
    """Active grants can be matched by actor, action, resource, risk, and scope."""
    service = DelegationService(autonomy_repository(), AllowPolicy())
    grant = service.create_grant(
        DelegationGrantRequest(
            actor_id="actor-1",
            workspace_id="workspace-1",
            delegated_by="actor-1",
            delegated_to="aion-system",
            owner_scope=["workspace:main"],
            mode="delegated_controlled",
            max_risk_level="medium",
            allowed_action_types=["capability.invoke"],
            resource_types=["capability"],
            reason="bounded delegation",
            expires_at=datetime.now(UTC) + timedelta(hours=1),
        )
    )

    matched = service.find_active_grant(
        "actor-1",
        "workspace-1",
        "capability.invoke",
        "capability",
        "medium",
        ["workspace:main"],
    )

    assert matched == grant


def test_delegation_service_revoke_blocks_future_matching() -> None:
    """Revoked delegations stop covering controlled actions."""
    service = DelegationService(autonomy_repository(), AllowPolicy())
    grant = service.create_grant(
        DelegationGrantRequest(
            reason="bounded delegation",
            owner_scope=["workspace:main"],
        )
    )

    service.revoke_grant(grant.delegation_id, "actor-1", "stop delegation")

    assert (
        service.find_active_grant(
            None,
            None,
            "capability.invoke",
            "capability",
            "low",
            ["workspace:main"],
        )
        is None
    )


def test_delegation_service_policy_deny_blocks_create() -> None:
    """Delegation creation passes through policy."""
    service = DelegationService(
        autonomy_repository(),
        AllowPolicy(deny_action="autonomy.delegation.create"),
    )

    try:
        service.create_grant(DelegationGrantRequest(reason="blocked delegation"))
    except PermissionError as exc:
        assert str(exc) == "denied"
    else:
        raise AssertionError("expected PermissionError")
