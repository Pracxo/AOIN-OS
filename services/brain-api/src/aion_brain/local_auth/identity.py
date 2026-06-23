"""Synthetic local operator identity construction."""

from __future__ import annotations

from uuid import uuid4

from aion_brain.contracts.local_auth import (
    DevIdentitySimulationRequest,
    LocalOperatorIdentity,
    utc_now,
)


def build_local_operator_identity(
    request: DevIdentitySimulationRequest,
) -> LocalOperatorIdentity:
    """Create a synthetic local operator identity without credentials."""
    return LocalOperatorIdentity(
        local_identity_id=f"local-identity-{uuid4().hex}",
        actor_id=request.actor_id,
        workspace_id=request.workspace_id,
        display_name=request.actor_id.replace(".", " ").title(),
        roles=request.roles,
        owner_scope=request.owner_scope,
        status="simulated",
        identity_source="local_dev",
        production_identity=False,
        credentials_present=False,
        metadata={
            **request.metadata,
            "synthetic": True,
            "session_present": False,
            "production_auth": False,
        },
        created_at=utc_now(),
    )


__all__ = ["build_local_operator_identity"]
