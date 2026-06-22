"""Generic local security control catalog."""

from __future__ import annotations

import builtins
from datetime import UTC, datetime
from typing import Any, cast
from uuid import uuid4

from aion_brain.api_support.errors import AIONNotFoundException, AIONPolicyDeniedException
from aion_brain.contracts.policy import PolicyRequest
from aion_brain.contracts.security_baseline import SecurityControlRecord
from aion_brain.policy.base import PolicyAdapter
from aion_brain.security_baseline.defaults import default_security_controls
from aion_brain.security_baseline.repository import SecurityBaselineRepository
from aion_brain.versioning.compatibility import emit_versioning_telemetry


class SecurityControlCatalog:
    """Manage generic local hardening controls."""

    def __init__(
        self,
        repository: SecurityBaselineRepository,
        policy_adapter: PolicyAdapter,
        *,
        telemetry_service: object | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._telemetry_service = telemetry_service

    def seed_defaults(
        self,
        dry_run: bool = True,
        actor_context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Seed or preview default security controls."""
        self._authorize(
            "security.control.create",
            ["workspace:main"],
            risk_level="medium",
            context=actor_context,
        )
        controls = default_security_controls()
        if not dry_run:
            for control in controls:
                self._repository.save_control(control)
            self._emit(
                "security_control_seeded",
                "security-control-defaults",
                ["workspace:main"],
                0.7,
                {"control_count": len(controls)},
            )
        return {
            "seeded": not dry_run,
            "dry_run": dry_run,
            "control_count": len(controls),
            "control_keys": [control.control_key for control in controls],
            "generic_only": True,
        }

    def create(self, record: SecurityControlRecord) -> SecurityControlRecord:
        """Create or replace one control."""
        self._authorize(
            "security.control.create",
            ["workspace:main"],
            resource_id=record.control_key,
            risk_level="medium",
            context=record.metadata,
        )
        saved = self._repository.save_control(record)
        self._emit(
            "security_control_updated",
            saved.control_key,
            ["workspace:main"],
            0.7,
            {"status": saved.status, "category": saved.category},
        )
        return saved

    def list(
        self,
        status: str | None = None,
        category: str | None = None,
        actor_context: dict[str, Any] | None = None,
    ) -> list[SecurityControlRecord]:
        """List controls."""
        self._authorize(
            "security.control.read",
            ["workspace:main"],
            context={"status": status, "category": category, **(actor_context or {})},
        )
        return self._repository.list_controls(status=status, category=category)

    def update_status(
        self,
        control_key: str,
        status: str,
        actor_id: str | None,
        reason: str,
        actor_context: dict[str, Any] | None = None,
    ) -> SecurityControlRecord:
        """Update one control status."""
        self._authorize(
            "security.control.update",
            ["workspace:main"],
            actor_id=actor_id,
            resource_id=control_key,
            risk_level="medium",
            context={"status": status, "reason": reason, **(actor_context or {})},
        )
        existing = self._repository.get_control(control_key)
        if existing is None:
            raise AIONNotFoundException("security_control_not_found")
        updated = existing.model_copy(
            update={
                "status": cast(Any, status),
                "updated_at": datetime.now(UTC),
                "metadata": {**existing.metadata, "last_status_reason": reason},
            }
        )
        saved = self._repository.save_control(updated)
        self._emit(
            "security_control_updated",
            saved.control_key,
            ["workspace:main"],
            0.7,
            {"status": saved.status},
        )
        return saved

    def _authorize(
        self,
        action_type: str,
        scope: builtins.list[str],
        *,
        actor_id: str | None = None,
        resource_id: str | None = None,
        risk_level: str = "low",
        context: dict[str, Any] | None = None,
    ) -> None:
        decision = self._policy_adapter.authorize(
            PolicyRequest(
                request_id=f"{action_type}-{uuid4().hex}",
                trace_id=None,
                actor_id=actor_id,
                workspace_id=None,
                action_type=action_type,
                resource_type="security_control",
                resource_id=resource_id,
                risk_level=risk_level,
                approval_present=True,
                requested_permissions=[action_type],
                security_scope=scope,
                context=context or {},
            )
        )
        if not decision.allow:
            raise AIONPolicyDeniedException(decision.reason)

    def _emit(
        self,
        event_type: str,
        node_id: str,
        scope: builtins.list[str],
        intensity: float,
        payload: dict[str, Any],
    ) -> None:
        emit_versioning_telemetry(
            self._telemetry_service,
            event_type=event_type,
            node_type="control",
            node_id=node_id,
            intensity=intensity,
            scope=scope,
            payload=payload,
        )
