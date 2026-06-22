"""Generic local threat model service."""

from __future__ import annotations

import builtins
from datetime import UTC, datetime
from typing import Any, cast
from uuid import uuid4

from aion_brain.api_support.errors import AIONNotFoundException, AIONPolicyDeniedException
from aion_brain.contracts.policy import PolicyRequest
from aion_brain.contracts.security_baseline import ThreatModelRecord
from aion_brain.policy.base import PolicyAdapter
from aion_brain.security_baseline.defaults import default_threat_model_records
from aion_brain.security_baseline.repository import SecurityBaselineRepository
from aion_brain.versioning.compatibility import emit_versioning_telemetry


class ThreatModelService:
    """Manage generic AION threat model records."""

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
        owner_scope: list[str] | None = None,
        actor_context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Seed or preview the default generic threat model."""
        scope = owner_scope or ["workspace:main"]
        self._authorize(
            "security.threat_model.create",
            scope,
            risk_level="medium",
            context=actor_context,
        )
        records = default_threat_model_records(scope)
        if not dry_run:
            for record in records:
                self._repository.save_threat_model(record)
            self._emit(
                "threat_model_seeded",
                "threat-model-defaults",
                scope,
                0.7,
                {"record_count": len(records)},
            )
        return {
            "seeded": not dry_run,
            "dry_run": dry_run,
            "threat_model_count": len(records),
            "threat_model_ids": [record.threat_model_id for record in records],
            "generic_only": True,
        }

    def create(self, record: ThreatModelRecord) -> ThreatModelRecord:
        """Create one threat model record."""
        self._authorize(
            "security.threat_model.create",
            record.owner_scope,
            actor_id=record.created_by,
            resource_id=record.threat_model_id,
            risk_level="medium",
            context=record.metadata,
        )
        saved = self._repository.save_threat_model(record)
        self._emit(
            "threat_model_created",
            saved.threat_model_id,
            saved.owner_scope,
            0.7,
            {"category": saved.category, "status": saved.status},
        )
        return saved

    def list(
        self,
        status: str | None = None,
        category: str | None = None,
        *,
        owner_scope: list[str] | None = None,
        actor_context: dict[str, Any] | None = None,
    ) -> list[ThreatModelRecord]:
        """List threat model records."""
        self._authorize(
            "security.threat_model.read",
            owner_scope or ["workspace:main"],
            context={"status": status, "category": category, **(actor_context or {})},
        )
        return self._repository.list_threat_models(status=status, category=category)

    def update_status(
        self,
        threat_model_id: str,
        status: str,
        actor_id: str | None,
        reason: str,
        *,
        owner_scope: builtins.list[str] | None = None,
        actor_context: dict[str, Any] | None = None,
    ) -> ThreatModelRecord:
        """Update one threat model status."""
        scope = owner_scope or ["workspace:main"]
        self._authorize(
            "security.threat_model.update",
            scope,
            actor_id=actor_id,
            resource_id=threat_model_id,
            risk_level="medium",
            context={"status": status, "reason": reason, **(actor_context or {})},
        )
        existing = self._repository.get_threat_model(threat_model_id)
        if existing is None:
            raise AIONNotFoundException("threat_model_not_found")
        now = datetime.now(UTC)
        updated = existing.model_copy(
            update={
                "status": cast(Any, status),
                "updated_at": now,
                "resolved_at": now if status in {"mitigated", "dismissed"} else None,
                "metadata": {**existing.metadata, "last_status_reason": reason},
            }
        )
        return self._repository.save_threat_model(updated)

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
                resource_type="threat_model",
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
            node_type="threat",
            node_id=node_id,
            intensity=intensity,
            scope=scope,
            payload=payload,
        )
