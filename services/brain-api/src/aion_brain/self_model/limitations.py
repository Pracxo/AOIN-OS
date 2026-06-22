"""Limitation ledger service."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, cast
from uuid import uuid4

from aion_brain.contracts.self_model import LimitationCreateRequest, LimitationRecord
from aion_brain.outcomes._shared import audit_optional, authorize, emit_telemetry
from aion_brain.self_model.defaults import default_limitation_requests
from aion_brain.self_model.repository import SelfModelRepository


class LimitationLedgerService:
    """Manage generic limitation records without mutating runtime behavior."""

    def __init__(
        self,
        repository: SelfModelRepository,
        policy_adapter: object,
        *,
        telemetry_service: object | None = None,
        audit_sink: object | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._telemetry_service = telemetry_service
        self._audit_sink = audit_sink

    def create_limitation(self, request: LimitationCreateRequest) -> LimitationRecord:
        authorize(
            self._policy_adapter,
            action_type="self_model.limitation.create",
            resource_type="limitation",
            resource_id=request.limitation_id,
            scope=request.owner_scope,
            risk_level="low",
            context={"category": request.category, "severity": request.severity},
        )
        now = datetime.now(UTC)
        record = LimitationRecord(
            limitation_id=request.limitation_id or f"limitation-{uuid4().hex}",
            limitation_key=request.limitation_key,
            category=request.category,
            status="active",
            severity=request.severity,
            title=request.title,
            description=request.description,
            affected_capabilities=request.affected_capabilities,
            workaround=request.workaround,
            disclosure_required=request.disclosure_required,
            owner_scope=request.owner_scope,
            metadata=request.metadata,
            created_by=request.created_by,
            created_at=now,
            updated_at=now,
        )
        stored = self._repository.save_limitation(record)
        audit_optional(
            self._audit_sink,
            "limitation_record_created",
            {"limitation_id": stored.limitation_id, "severity": stored.severity},
        )
        emit_telemetry(
            self._telemetry_service,
            event_type="limitation_record_created",
            node_type="limitation",
            node_id=stored.limitation_id,
            intensity=_limitation_intensity(stored.severity),
            trace_id=None,
            payload={"owner_scope": stored.owner_scope, "severity": stored.severity},
        )
        return stored

    def list_limitations(
        self,
        scope: list[str],
        *,
        status: str | None = None,
        category: str | None = None,
        severity: str | None = None,
        disclosure_required: bool | None = None,
    ) -> list[LimitationRecord]:
        authorize(
            self._policy_adapter,
            action_type="self_model.limitation.read",
            resource_type="limitation",
            resource_id=None,
            scope=scope,
            risk_level="low",
        )
        return self._repository.list_limitations(
            scope,
            status=status,
            category=category,
            severity=severity,
            disclosure_required=disclosure_required,
        )

    def resolve_limitation(
        self,
        limitation_id: str,
        actor_id: str | None,
        reason: str,
    ) -> LimitationRecord:
        existing = self._repository.get_limitation(limitation_id)
        if existing is None:
            raise ValueError("limitation_not_found")
        authorize(
            self._policy_adapter,
            action_type="self_model.limitation.update",
            resource_type="limitation",
            resource_id=limitation_id,
            scope=existing.owner_scope,
            actor_id=actor_id,
            risk_level="low",
            context={"reason": reason},
        )
        resolved = existing.model_copy(
            update={
                "status": cast(Any, "resolved"),
                "resolved_at": datetime.now(UTC),
                "updated_at": datetime.now(UTC),
                "metadata": {
                    **existing.metadata,
                    "resolve_reason": reason,
                    "resolved_by": actor_id,
                },
            }
        )
        stored = self._repository.save_limitation(resolved)
        audit_optional(
            self._audit_sink,
            "limitation_record_resolved",
            {"limitation_id": stored.limitation_id, "actor_id": actor_id},
        )
        emit_telemetry(
            self._telemetry_service,
            event_type="limitation_record_resolved",
            node_type="limitation",
            node_id=stored.limitation_id,
            intensity=0.4,
            trace_id=None,
            payload={"owner_scope": stored.owner_scope, "status": stored.status},
        )
        return stored

    def seed_defaults(self, scope: list[str], dry_run: bool = True) -> dict[str, Any]:
        requests = default_limitation_requests(scope)
        created: list[LimitationRecord] = []
        skipped: list[str] = []
        for request in requests:
            existing = self._repository.get_limitation_by_key(request.limitation_key)
            if existing is not None:
                skipped.append(request.limitation_key)
                continue
            if not dry_run:
                created.append(self.create_limitation(request))
        return {
            "dry_run": dry_run,
            "default_count": len(requests),
            "created_count": len(created),
            "skipped": skipped,
            "limitations": [
                item.model_dump(mode="json") for item in (created if not dry_run else requests)
            ],
        }

    def status(self, scope: list[str] | None = None) -> dict[str, Any]:
        items = self.list_limitations(scope or ["workspace:main"], status="active")
        critical = sum(1 for item in items if item.severity == "critical")
        return {
            "status": "failed" if critical else ("warning" if items else "healthy"),
            "limitation_count": len(items),
            "critical_limitation_count": critical,
        }


def _limitation_intensity(severity: str) -> float:
    if severity == "critical":
        return 1.0
    if severity == "high":
        return 0.7
    return 0.4
