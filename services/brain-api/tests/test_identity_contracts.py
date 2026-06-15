"""Identity contract tests."""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from aion_brain.contracts.identity import (
    ActorRecord,
    PermissionGrant,
    WorkspaceMembership,
    WorkspaceRecord,
)


def test_actor_record_validates_type_status_and_secret_metadata() -> None:
    """ActorRecord validates generic actor metadata."""
    actor = make_actor()

    assert actor.actor_type == "user"
    with pytest.raises(ValidationError):
        ActorRecord(
            actor_id="actor-1",
            actor_type="person",
            display_name="Actor",
            status="active",
            metadata={},
        )
    with pytest.raises(ValidationError):
        ActorRecord(
            actor_id="actor-1",
            actor_type="user",
            display_name="Actor",
            status="active",
            metadata={"api_key": "hidden"},
        )


def test_workspace_record_validates_status() -> None:
    """Workspace status is constrained."""
    assert make_workspace().status == "active"
    with pytest.raises(ValidationError):
        WorkspaceRecord(
            workspace_id="workspace-1",
            name="Main",
            status="pending",
            owner_actor_id=None,
            metadata={},
        )


def test_workspace_membership_validates_role() -> None:
    """Membership role is constrained."""
    assert make_membership().role == "owner"
    with pytest.raises(ValidationError):
        WorkspaceMembership(
            membership_id="membership-1",
            workspace_id="workspace-1",
            actor_id="actor-1",
            role="auditor",
            status="active",
            metadata={},
        )


def test_permission_grant_validates_effect_resource_and_permission() -> None:
    """Permission grants stay generic."""
    assert make_grant().effect == "allow"
    with pytest.raises(ValidationError):
        PermissionGrant(
            grant_id="grant-1",
            actor_id="actor-1",
            permission="memory",
            resource_type="memory",
            effect="allow",
            status="active",
            metadata={},
        )
    with pytest.raises(ValidationError):
        PermissionGrant(
            grant_id="grant-1",
            actor_id="actor-1",
            permission="memory.read",
            resource_type="finance",
            effect="allow",
            status="active",
            metadata={},
        )


def make_actor(actor_id: str = "actor-1", status: str = "active") -> ActorRecord:
    """Create an actor."""
    now = datetime.now(UTC)
    return ActorRecord(
        actor_id=actor_id,
        actor_type="user",
        display_name="Actor One",
        status=status,
        metadata={},
        created_at=now,
        updated_at=now,
    )


def make_workspace(
    workspace_id: str = "workspace-1",
    status: str = "active",
) -> WorkspaceRecord:
    """Create a workspace."""
    now = datetime.now(UTC)
    return WorkspaceRecord(
        workspace_id=workspace_id,
        name="Main",
        status=status,
        owner_actor_id="actor-1",
        metadata={},
        created_at=now,
        updated_at=now,
    )


def make_membership(
    membership_id: str = "membership-1",
    role: str = "owner",
    status: str = "active",
) -> WorkspaceMembership:
    """Create a membership."""
    now = datetime.now(UTC)
    return WorkspaceMembership(
        membership_id=membership_id,
        workspace_id="workspace-1",
        actor_id="actor-1",
        role=role,
        status=status,
        granted_by="actor-1",
        metadata={},
        created_at=now,
        updated_at=now,
    )


def make_grant(
    grant_id: str = "grant-1",
    permission: str = "memory.read",
    effect: str = "allow",
    status: str = "active",
    actor_id: str | None = "actor-1",
    workspace_id: str | None = None,
    role: str | None = None,
) -> PermissionGrant:
    """Create a permission grant."""
    return PermissionGrant(
        grant_id=grant_id,
        actor_id=actor_id,
        workspace_id=workspace_id,
        role=role,
        permission=permission,
        resource_type="memory",
        resource_id=None,
        effect=effect,
        status=status,
        granted_by="actor-1",
        expires_at=None,
        metadata={},
        created_at=datetime.now(UTC),
    )
