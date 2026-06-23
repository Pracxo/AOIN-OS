"""Local auth role permission mapping."""

from __future__ import annotations

from aion_brain.contracts.local_auth import RolePermission
from aion_brain.operator_console.action_boundaries import forbidden_action_descriptors
from aion_brain.operator_console.data_sources import list_console_views

_COMMON_CONSTRAINTS = [
    "dev_only",
    "read_only_console",
    "no_execute",
    "no_activation",
    "no_external_calls",
    "no_hard_delete",
]
_DRY_RUN_ACTIONS = [
    "run_dry_run_check",
    "acknowledge_notification",
    "dismiss_non_blocking_finding_with_reason",
]
_REVIEW_ACTIONS = ["create_review_record"]


class LocalRoleService:
    """Return deterministic dev-only local role permissions."""

    def default_permissions(self) -> list[RolePermission]:
        """Return the full local auth role matrix."""
        views = [str(view) for view in list_console_views()]
        audit_views = ["audit_provenance", "settings_safety", "overview"]
        forbidden = [item.action_key for item in forbidden_action_descriptors()]
        return [
            RolePermission(
                role="viewer",
                read_views=views,
                dry_run_actions=[],
                review_actions=[],
                forbidden_actions=forbidden,
                constraints=[*_COMMON_CONSTRAINTS, "read_only"],
                metadata={"production_auth": False},
            ),
            RolePermission(
                role="operator",
                read_views=views,
                dry_run_actions=_DRY_RUN_ACTIONS,
                review_actions=[],
                forbidden_actions=forbidden,
                constraints=[*_COMMON_CONSTRAINTS, "dry_run_only"],
                metadata={"production_auth": False},
            ),
            RolePermission(
                role="reviewer",
                read_views=views,
                dry_run_actions=[],
                review_actions=_REVIEW_ACTIONS,
                forbidden_actions=forbidden,
                constraints=[*_COMMON_CONSTRAINTS, "review_record_only"],
                metadata={"production_auth": False},
            ),
            RolePermission(
                role="admin",
                read_views=views,
                dry_run_actions=[],
                review_actions=[],
                forbidden_actions=forbidden,
                constraints=[*_COMMON_CONSTRAINTS, "future_design_settings_only"],
                metadata={"settings_mutation_enabled": False},
            ),
            RolePermission(
                role="auditor",
                read_views=audit_views,
                dry_run_actions=[],
                review_actions=[],
                forbidden_actions=forbidden,
                constraints=[*_COMMON_CONSTRAINTS, "audit_read_only"],
                metadata={"production_auth": False},
            ),
            RolePermission(
                role="system_service",
                read_views=["overview", "settings_safety"],
                dry_run_actions=[],
                review_actions=[],
                forbidden_actions=forbidden,
                constraints=[*_COMMON_CONSTRAINTS, "synthetic_system_context"],
                metadata={"production_auth": False},
            ),
        ]

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
