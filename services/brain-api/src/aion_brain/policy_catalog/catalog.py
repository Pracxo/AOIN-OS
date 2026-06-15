"""Policy action catalog service."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from aion_brain.contracts.policy import PolicyRequest
from aion_brain.contracts.policy_catalog import PolicyActionCatalogEntry
from aion_brain.policy.base import PolicyAdapter
from aion_brain.policy_catalog.defaults import default_action_catalog_entries
from aion_brain.policy_catalog.repository import PolicyCatalogRepository
from aion_brain.policy_catalog.telemetry import emit_policy_telemetry


class PolicyCatalogService:
    """Manage the generic AION policy action vocabulary."""

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

    def create_action(self, entry: PolicyActionCatalogEntry) -> PolicyActionCatalogEntry:
        """Create or update one policy action catalog entry."""
        self._authorize("policy.catalog.create", "policy_catalog", entry.policy_action_id, "medium")
        saved = self._repository.save_action(entry)
        self._emit(
            "policy_action_registered",
            "policy",
            saved.policy_action_id,
            0.5,
            {"action_type": saved.action_type, "category": saved.category},
        )
        return saved

    def list_actions(
        self,
        category: str | None = None,
        status: str | None = None,
    ) -> list[PolicyActionCatalogEntry]:
        """List policy actions."""
        self._authorize("policy.catalog.read", "policy_catalog", None, "low")
        return self._repository.list_actions(category=category, status=status)

    def get_action(self, action_type: str) -> PolicyActionCatalogEntry | None:
        """Return one action by action type."""
        self._authorize("policy.catalog.read", "policy_catalog", action_type, "low")
        return self._repository.get_action(action_type)

    def disable_action(
        self,
        action_type: str,
        actor_id: str | None,
        reason: str,
    ) -> PolicyActionCatalogEntry:
        """Disable one action catalog entry."""
        entry = self._repository.get_action(action_type)
        if entry is None:
            raise ValueError("policy_action_not_found")
        self._authorize(
            "policy.catalog.update",
            "policy_catalog",
            entry.policy_action_id,
            "medium",
            actor_id=actor_id,
        )
        saved = self._repository.save_action(
            entry.model_copy(
                update={
                    "status": "disabled",
                    "disabled_at": datetime.now(UTC),
                    "metadata": {**entry.metadata, "disabled_reason": reason},
                }
            )
        )
        return saved

    def seed_defaults(self, dry_run: bool = True) -> dict[str, Any]:
        """Seed default action catalog entries when explicitly requested."""
        defaults = default_action_catalog_entries()
        self._authorize("policy.catalog.create", "policy_catalog", None, "medium")
        if dry_run:
            return {
                "dry_run": True,
                "action_count": len(defaults),
                "would_create": [entry.action_type for entry in defaults],
            }
        for entry in defaults:
            self._repository.save_action(entry)
        self._emit(
            "policy_catalog_seeded",
            "policy",
            "policy-catalog-defaults",
            0.6,
            {"action_count": len(defaults)},
        )
        return {"dry_run": False, "action_count": len(defaults), "created": True}

    def _authorize(
        self,
        action_type: str,
        resource_type: str,
        resource_id: str | None,
        risk_level: str,
        *,
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
