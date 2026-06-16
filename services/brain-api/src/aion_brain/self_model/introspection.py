"""Introspection snapshot service."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from aion_brain.contracts.confidence import IntrospectionSnapshot, IntrospectionSnapshotRequest
from aion_brain.outcomes._shared import authorize, emit_telemetry, scope_matches
from aion_brain.self_model.repository import SelfModelRepository


class IntrospectionSnapshotService:
    """Create and read redacted self-model introspection snapshots."""

    def __init__(
        self,
        repository: SelfModelRepository,
        policy_adapter: object,
        *,
        profile_service: Any,
        capability_awareness_service: Any,
        limitation_service: Any,
        confidence_calibrator: Any,
        settings: object | None = None,
        telemetry_service: object | None = None,
        operator_service: object | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._profile_service = profile_service
        self._capability_awareness_service = capability_awareness_service
        self._limitation_service = limitation_service
        self._confidence_calibrator = confidence_calibrator
        self._settings = settings
        self._telemetry_service = telemetry_service
        self._operator_service = operator_service

    def set_operator_service(self, operator_service: object) -> None:
        self._operator_service = operator_service

    def create_snapshot(self, request: IntrospectionSnapshotRequest) -> IntrospectionSnapshot:
        authorize(
            self._policy_adapter,
            action_type="self_model.introspection.create",
            resource_type="introspection_snapshot",
            resource_id=request.introspection_snapshot_id,
            scope=request.owner_scope,
            trace_id=request.trace_id,
            actor_id=request.actor_id,
            workspace_id=request.workspace_id,
            risk_level="low",
            context={"snapshot_type": request.snapshot_type},
        )
        profile = self._profile_service.get_active_profile(request.owner_scope)
        capabilities = self._capability_awareness_service.refresh(request.owner_scope, dry_run=True)
        limitations = self._limitation_service.list_limitations(
            request.owner_scope, status="active"
        )
        calibrations = self._confidence_calibrator.list_calibrations(
            trace_id=request.trace_id,
            limit=100,
        )
        snapshot = IntrospectionSnapshot(
            introspection_snapshot_id=(
                request.introspection_snapshot_id or f"introspection-{uuid4().hex}"
            ),
            trace_id=request.trace_id,
            actor_id=request.actor_id,
            workspace_id=request.workspace_id,
            snapshot_type=request.snapshot_type,
            status="created",
            owner_scope=request.owner_scope,
            self_model=profile.model_dump(mode="json"),
            capability_inventory=capabilities,
            limitations=limitations,
            calibration_summary={
                "count": len(calibrations),
                "low_count": sum(1 for item in calibrations if item.confidence_level == "low"),
                "latest_calibration_id": calibrations[0].calibration_id if calibrations else None,
            },
            operator_summary=_operator_summary(self._operator_service, request)
            if request.include_operator_summary
            else {},
            config_summary=_config_summary(self._settings)
            if request.include_config_summary
            else {},
            audit_refs=[] if request.include_audit_refs else [],
            metadata=request.metadata,
            created_by=request.created_by,
            created_at=datetime.now(UTC),
        )
        stored = self._repository.save_introspection_snapshot(snapshot)
        emit_telemetry(
            self._telemetry_service,
            event_type="introspection_snapshot_created",
            node_type="introspection",
            node_id=stored.introspection_snapshot_id,
            intensity=0.6,
            trace_id=stored.trace_id,
            payload={"owner_scope": stored.owner_scope, "snapshot_type": stored.snapshot_type},
        )
        return stored

    def get_snapshot(
        self,
        introspection_snapshot_id: str,
        scope: list[str],
    ) -> IntrospectionSnapshot | None:
        authorize(
            self._policy_adapter,
            action_type="self_model.introspection.read",
            resource_type="introspection_snapshot",
            resource_id=introspection_snapshot_id,
            scope=scope,
            risk_level="low",
        )
        snapshot = self._repository.get_introspection_snapshot(introspection_snapshot_id)
        if snapshot is None or not scope_matches(snapshot.owner_scope, scope):
            return None
        return snapshot

    def list_snapshots(
        self,
        scope: list[str],
        *,
        snapshot_type: str | None = None,
        status: str | None = None,
        limit: int = 50,
    ) -> list[IntrospectionSnapshot]:
        authorize(
            self._policy_adapter,
            action_type="self_model.introspection.read",
            resource_type="introspection_snapshot",
            resource_id=None,
            scope=scope,
            risk_level="low",
        )
        return self._repository.list_introspection_snapshots(
            scope,
            snapshot_type=snapshot_type,
            status=status,
            limit=limit,
        )


def _config_summary(settings: object | None) -> dict[str, Any]:
    if settings is None:
        return {}
    return {
        "env": str(getattr(settings, "env", "unknown")),
        "version": str(getattr(settings, "version", "unknown")),
        "self_model_enabled": bool(getattr(settings, "self_model_enabled", True)),
        "model_gateway_enabled": bool(getattr(settings, "model_gateway_enabled", False)),
        "observability_adapter": str(getattr(settings, "observability_adapter", "local")),
        "redacted": True,
    }


def _operator_summary(
    operator_service: object | None,
    request: IntrospectionSnapshotRequest,
) -> dict[str, Any]:
    overview = getattr(operator_service, "overview", None)
    if not callable(overview):
        return {"available": False}
    try:
        from aion_brain.contracts.operator import OperatorOverviewRequest

        result = overview(
            OperatorOverviewRequest(
                trace_id=request.trace_id,
                actor_id=request.actor_id,
                workspace_id=request.workspace_id,
                owner_scope=request.owner_scope,
                include_runbooks=False,
            )
        )
        return {
            "available": True,
            "overall_status": getattr(result, "overall_status", "unknown"),
            "card_count": len(getattr(result, "cards", [])),
            "action_count": len(getattr(result, "actions", [])),
        }
    except Exception:
        return {"available": False}
