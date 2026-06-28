"""Local auth role permission mapping."""

from __future__ import annotations

from typing import Any

from aion_brain.contracts.local_auth import RoleAccessAudit, RoleAccessDecision, RolePermission
from aion_brain.local_auth.permission_matrix import RolePermissionMatrixService


class LocalRoleService:
    """Return deterministic dev-only local role permissions."""

    def __init__(
        self,
        *,
        matrix_service: RolePermissionMatrixService | None = None,
    ) -> None:
        self.matrix_service = matrix_service or RolePermissionMatrixService()

    def default_permissions(self) -> list[RolePermission]:
        """Return the full local auth role matrix."""
        return self.matrix_service.role_permissions()

    def permissions_for_roles(self, roles: list[str]) -> dict[str, object]:
        """Return merged permissions for one or more local auth roles."""
        selected = [item for item in self.default_permissions() if item.role in set(roles)]
        return {
            "roles": sorted({item.role for item in selected}),
            "read_views": sorted({view for item in selected for view in item.read_views}),
            "dry_run_actions": sorted(
                {action for item in selected for action in item.dry_run_actions}
            ),
            "review_actions": sorted(
                {action for item in selected for action in item.review_actions}
            ),
            "forbidden_actions": sorted(
                {action for item in selected for action in item.forbidden_actions}
            ),
            "constraints": sorted(
                {constraint for item in selected for constraint in item.constraints}
            ),
            "execute_allowed": False,
            "activation_allowed": False,
            "external_calls_allowed": False,
            "hard_delete_allowed": False,
        }

    def build_permission_matrix(self) -> dict[str, Any]:
        """Return the AION-096 role permission proof matrix."""
        return self.matrix_service.build_permission_matrix()

    def decide(
        self,
        role: str,
        view: str,
        section_key: str | None = None,
        action_key: str | None = None,
    ) -> RoleAccessDecision:
        """Return one fail-closed role access decision."""
        return self.matrix_service.decide(
            role,
            view,
            section_key=section_key,
            action_key=action_key,
        )

    def filter_view_for_roles(
        self,
        view_model: dict[str, Any],
        roles: list[str],
    ) -> dict[str, Any]:
        """Return a role-filtered read-only console view model."""
        return self.matrix_service.filter_view_for_roles(view_model, roles)

    def audit_matrix(self, trace_id: str | None = None) -> RoleAccessAudit:
        """Audit the role matrix safety invariants."""
        return self.matrix_service.audit_matrix(trace_id=trace_id)

    def role_allows_view(self, role: str, view: str) -> bool:
        """Return whether a role can read a console view."""
        return any(
            permission.role == role and view in permission.read_views
            for permission in self.default_permissions()
        )

    def role_allows_dry_run(self, role: str, action_key: str) -> bool:
        """Return whether a role can request a descriptor-only dry-run action."""
        return any(
            permission.role == role and action_key in permission.dry_run_actions
            for permission in self.default_permissions()
        )

    def role_allows_review(self, role: str, action_key: str) -> bool:
        """Return whether a role can create a review record."""
        return any(
            permission.role == role and action_key in permission.review_actions
            for permission in self.default_permissions()
        )


__all__ = ["LocalRoleService"]
