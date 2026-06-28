"""Local session context derivation."""

from __future__ import annotations

from aion_brain.contracts.local_auth import DevIdentitySimulationRequest
from aion_brain.contracts.local_session import LocalSessionContext, LocalSessionPreview, utc_now
from aion_brain.local_auth.context import build_local_auth_context
from aion_brain.local_auth.identity import build_local_operator_identity
from aion_brain.local_auth.roles import LocalRoleService


class LocalSessionContextService:
    """Build read-only role-aware local session contexts from previews."""

    def __init__(self, *, role_service: LocalRoleService | None = None) -> None:
        self._role_service = role_service or LocalRoleService()

    def build_context(self, preview: LocalSessionPreview) -> LocalSessionContext:
        """Return local session context with hard-disabled privileged flags."""
        merged = self._role_service.permissions_for_roles(preview.roles)
        auth_context = build_local_auth_context(
            build_local_operator_identity(_preview_as_identity_request(preview)),
            trace_id=preview.trace_id,
            role_service=self._role_service,
        )
        return LocalSessionContext(
            local_session_preview_id=preview.local_session_preview_id,
            auth_context_id=auth_context.local_auth_context_id,
            actor_id=preview.actor_id,
            workspace_id=preview.workspace_id,
            roles=preview.roles,
            owner_scope=preview.owner_scope,
            read_allowed=bool(merged.get("read_views")),
            dry_run_allowed=bool(merged.get("dry_run_actions")),
            review_allowed=bool(merged.get("review_actions")),
            write_allowed=False,
            execute_allowed=False,
            activation_allowed=False,
            external_calls_allowed=False,
            session_valid=preview.status == "active_local_preview",
            session_read_only=True,
            metadata={
                "synthetic": True,
                "dev_only": True,
                "role_matrix_version": "aion-096",
                "action_authz_boundary": "dry_run_preview_and_review_only",
                "role_constraints": merged.get("constraints", []),
            },
            created_at=utc_now(),
        )


def _preview_as_identity_request(preview: LocalSessionPreview) -> DevIdentitySimulationRequest:
    return DevIdentitySimulationRequest(
        trace_id=preview.trace_id,
        actor_id=preview.actor_id,
        workspace_id=preview.workspace_id,
        roles=preview.roles,
        owner_scope=preview.owner_scope,
        metadata={"source": "local_session_context"},
    )


__all__ = ["LocalSessionContextService"]
