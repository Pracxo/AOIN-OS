"""Operator snapshot service."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from aion_brain.contracts.operator import (
    OperatorOverviewRequest,
    OperatorSnapshot,
    OperatorSnapshotRequest,
)
from aion_brain.contracts.policy import PolicyRequest
from aion_brain.operator.action_center import _emit
from aion_brain.operator.control_tower import OperatorControlTowerService
from aion_brain.operator.repository import OperatorRepository


class OperatorSnapshotService:
    """Create and read local operator snapshots."""

    def __init__(
        self,
        repository: OperatorRepository,
        control_tower: OperatorControlTowerService,
        policy_adapter: object | None = None,
        telemetry_service: object | None = None,
    ) -> None:
        self._repository = repository
        self._control_tower = control_tower
        self._policy_adapter = policy_adapter
        self._telemetry_service = telemetry_service

    def create_snapshot(self, request: OperatorSnapshotRequest) -> OperatorSnapshot:
        """Create a local metadata-only operator snapshot."""
        self._authorize("operator.snapshot.create", request.owner_scope, None)
        overview = self._control_tower.overview(
            OperatorOverviewRequest(
                actor_id=request.actor_id,
                workspace_id=request.workspace_id,
                owner_scope=request.owner_scope,
                include_actions=request.include_actions,
                include_readiness=request.include_readiness,
            )
        )
        readiness = (
            self._control_tower.readiness(request.owner_scope)
            if request.include_readiness
            else None
        )
        snapshot = OperatorSnapshot(
            operator_snapshot_id=request.operator_snapshot_id or f"operator-snapshot-{uuid4().hex}",
            trace_id=overview.trace_id,
            actor_id=request.actor_id,
            workspace_id=request.workspace_id,
            snapshot_type=request.snapshot_type,
            status="created",
            owner_scope=request.owner_scope,
            overview=overview,
            action_items=overview.actions if request.include_actions else [],
            queue_summaries=overview.queues,
            readiness=readiness,
            generated_by=request.generated_by,
            created_at=datetime.now(UTC),
        )
        stored = self._repository.save_snapshot(snapshot)
        _emit(
            self._telemetry_service,
            "operator_snapshot_created",
            "operator",
            stored.operator_snapshot_id,
            0.5,
            {"snapshot_type": stored.snapshot_type, "status": stored.status},
            stored.trace_id,
        )
        return stored

    def get_snapshot(self, operator_snapshot_id: str, scope: list[str]) -> OperatorSnapshot | None:
        """Return one local snapshot when visible to scope."""
        self._authorize("operator.snapshot.read", scope, operator_snapshot_id)
        snapshot = self._repository.get_snapshot(operator_snapshot_id)
        if snapshot is None or not set(snapshot.owner_scope).intersection(scope):
            return None
        return snapshot

    def list_snapshots(
        self,
        scope: list[str],
        snapshot_type: str | None = None,
        status: str | None = None,
        limit: int = 50,
    ) -> list[OperatorSnapshot]:
        """List local snapshots."""
        self._authorize("operator.snapshot.read", scope, None)
        return self._repository.list_snapshots(
            scope=scope,
            snapshot_type=snapshot_type,
            status=status,
            limit=limit,
        )

    def _authorize(self, action_type: str, scope: list[str], resource_id: str | None) -> None:
        authorize = getattr(self._policy_adapter, "authorize", None)
        if not callable(authorize):
            return
        decision = authorize(
            PolicyRequest(
                request_id=f"operator-snapshot-{uuid4().hex}",
                trace_id=None,
                actor_id=None,
                workspace_id=None,
                action_type=action_type,
                resource_type="operator_snapshot",
                resource_id=resource_id,
                risk_level="low",
                approval_present=False,
                requested_permissions=[action_type],
                security_scope=scope,
                context={"source": "operator_snapshot_service"},
            )
        )
        if not decision.allow:
            raise PermissionError(decision.reason)
