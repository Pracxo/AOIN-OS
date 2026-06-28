"""Mock-claims actor mapping preview helpers."""

from __future__ import annotations

from typing import Any

from aion_brain.contracts.auth_runtime import MockClaimsPreviewRequest
from aion_brain.local_auth.roles import LocalRoleService


def build_actor_context_preview(
    request: MockClaimsPreviewRequest,
    role_service: LocalRoleService,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Return a preview-only actor context and role decisions."""

    role_decisions = role_service.permissions_for_roles(request.roles)
    actor_preview = {
        "actor_id": f"mock.{request.subject}",
        "subject": request.subject,
        "issuer": request.issuer,
        "audience": request.audience,
        "workspace_id": request.workspace_id,
        "roles": request.roles,
        "owner_scope": request.owner_scope,
        "preview_only": True,
        "authenticated": False,
        "auth_source": "mock_claims_preview",
        "policy_authoritative": False,
        "read_allowed": bool(role_decisions.get("read_views")),
        "dry_run_allowed": bool(role_decisions.get("dry_run_actions")),
        "review_allowed": bool(role_decisions.get("review_actions")),
        "write_allowed": False,
        "execute_allowed": False,
        "activation_allowed": False,
        "external_calls_allowed": False,
    }
    role_preview = {
        "roles": role_decisions.get("roles", []),
        "read_views": role_decisions.get("read_views", []),
        "dry_run_actions": role_decisions.get("dry_run_actions", []),
        "review_actions": role_decisions.get("review_actions", []),
        "forbidden_actions": role_decisions.get("forbidden_actions", []),
        "constraints": role_decisions.get("constraints", []),
        "write_allowed": False,
        "execute_allowed": False,
        "activation_allowed": False,
        "external_calls_allowed": False,
        "matrix_version": "aion-099-preview",
    }
    return actor_preview, role_preview


__all__ = ["build_actor_context_preview"]
