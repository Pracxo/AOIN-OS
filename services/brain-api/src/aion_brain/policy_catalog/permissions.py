"""Permission matrix and role template services."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from aion_brain.contracts.policy import PolicyRequest
from aion_brain.contracts.policy_catalog import PermissionCatalogEntry, RoleTemplate
from aion_brain.policy.base import PolicyAdapter
from aion_brain.policy_catalog.defaults import (
    default_permission_catalog_entries,
    default_role_templates,
)
from aion_brain.policy_catalog.repository import PolicyCatalogRepository
from aion_brain.policy_catalog.telemetry import emit_policy_telemetry


class PermissionMatrixService:
    """Manage generic permissions and role templates."""

    def __init__(
        self,
        *,
        repository: PolicyCatalogRepository,
        policy_adapter: PolicyAdapter,
        telemetry_service: object | None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._telemetry_service = telemetry_service

    def create_permission(self, entry: PermissionCatalogEntry) -> PermissionCatalogEntry:
        """Create or update one permission."""
        self._authorize("policy.permission.create", "permission_catalog", entry.permission_id)
        saved = self._repository.save_permission(entry)
        self._emit(
            "permission_registered",
            "permission",
            saved.permission_id,
            0.5,
            {"permission": saved.permission, "category": saved.category},
        )
        return saved

    def list_permissions(
        self,
        category: str | None = None,
        status: str | None = None,
    ) -> list[PermissionCatalogEntry]:
        """List permissions."""
        self._authorize("policy.permission.read", "permission_catalog", None, risk_level="low")
        return self._repository.list_permissions(category=category, status=status)

    def get_permission(self, permission: str) -> PermissionCatalogEntry | None:
        """Return one permission."""
        self._authorize(
            "policy.permission.read",
            "permission_catalog",
            permission,
            risk_level="low",
        )
        return self._repository.get_permission(permission)

    def disable_permission(
        self,
        permission: str,
        actor_id: str | None,
        reason: str,
    ) -> PermissionCatalogEntry:
        """Disable one permission."""
        entry = self._repository.get_permission(permission)
        if entry is None:
            raise ValueError("permission_not_found")
        self._authorize(
            "policy.permission.update",
            "permission_catalog",
            entry.permission_id,
            actor_id=actor_id,
        )
        return self._repository.save_permission(
            entry.model_copy(
                update={
                    "status": "disabled",
                    "disabled_at": datetime.now(UTC),
                    "metadata": {**entry.metadata, "disabled_reason": reason},
                }
            )
        )

    def create_role_template(self, template: RoleTemplate) -> RoleTemplate:
        """Create or update one role template."""
        self._authorize("policy.role_template.create", "role_template", template.role_template_id)
        saved = self._repository.save_role_template(template)
        self._emit(
            "role_template_registered",
            "role",
            saved.role_template_id,
            0.5,
            {"role_name": saved.role_name},
        )
        return saved

    def list_role_templates(self, status: str | None = None) -> list[RoleTemplate]:
        """List role templates."""
        self._authorize("policy.role_template.read", "role_template", None, risk_level="low")
        return self._repository.list_role_templates(status=status)

    def get_role_template(self, role_name: str) -> RoleTemplate | None:
        """Return one role template."""
        self._authorize("policy.role_template.read", "role_template", role_name, risk_level="low")
        return self._repository.get_role_template(role_name)

    def seed_default_roles(self, dry_run: bool = True) -> dict[str, Any]:
        """Seed default permissions and roles when explicitly requested."""
        permissions = default_permission_catalog_entries()
        roles = default_role_templates()
        self._authorize("policy.role_template.create", "role_template", None)
        if dry_run:
            return {
                "dry_run": True,
                "permission_count": len(permissions),
                "role_template_count": len(roles),
                "roles": [role.role_name for role in roles],
            }
        for permission in permissions:
            self._repository.save_permission(permission)
        for role in roles:
            self._repository.save_role_template(role)
            self._emit(
                "role_template_registered",
                "role",
                role.role_template_id,
                0.5,
                {"role_name": role.role_name},
            )
        return {
            "dry_run": False,
            "permission_count": len(permissions),
            "role_template_count": len(roles),
            "created": True,
        }

    def _authorize(
        self,
        action_type: str,
        resource_type: str,
        resource_id: str | None,
        *,
        risk_level: str = "medium",
        actor_id: str | None = None,
    ) -> None:
        decision = self._policy_adapter.authorize(
            PolicyRequest(
                request_id=f"{action_type}-{resource_id or uuid4().hex}",
                trace_id=None,
                actor_id=actor_id,
                workspace_id=None,
                action_type=action_type,
                resource_type=resource_type,
                resource_id=resource_id,
                risk_level=risk_level,
                approval_present=True,
                requested_permissions=[action_type],
                security_scope=["workspace:main"],
                context={},
            )
        )
        if not decision.allow:
            raise PermissionError(f"policy_denied:{decision.reason}")

    def _emit(
        self,
        event_type: str,
        node_type: str,
        node_id: str,
        intensity: float,
        payload: dict[str, Any],
    ) -> None:
        emit_policy_telemetry(
            self._telemetry_service,
            event_type=event_type,
            node_type=node_type,
            node_id=node_id,
            intensity=intensity,
            payload=payload,
        )
