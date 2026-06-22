"""Consistency checker for retry-safe Brain operations."""

from datetime import UTC, datetime, timedelta
from typing import cast
from uuid import uuid4

from aion_brain.config import Settings
from aion_brain.consistency.leases import ProcessingLeaseService
from aion_brain.consistency.repository import ConsistencyRepository
from aion_brain.contracts.consistency import (
    ConsistencyCheckRequest,
    ConsistencyCheckResult,
    ConsistencyCheckStatus,
)
from aion_brain.contracts.telemetry import (
    VisualTelemetryEvent,
    VisualTelemetryEventType,
)


class ConsistencyChecker:
    """Run safe consistency checks without executing commands or deliveries."""

    def __init__(
        self,
        *,
        repository: ConsistencyRepository,
        lease_service: ProcessingLeaseService,
        command_repository: object | None = None,
        outbox_service: object | None = None,
        inbox_service: object | None = None,
        idempotency_service: object | None = None,
        boundary_checker: object | None = None,
        telemetry_service: object | None = None,
        settings: Settings,
    ) -> None:
        self._repository = repository
        self._lease_service = lease_service
        self._command_repository = command_repository
        self._outbox_service = outbox_service
        self._inbox_service = inbox_service
        self._idempotency_service = idempotency_service
        self._boundary_checker = boundary_checker
        self._telemetry_service = telemetry_service
        self._settings = settings

    def run(self, request: ConsistencyCheckRequest) -> ConsistencyCheckResult:
        """Run one consistency check and persist the result."""
        if not self._settings.consistency_checker_enabled:
            raise PermissionError("consistency_checker_disabled")
        self._emit("consistency_check_started", "consistency-check-started", 0.4, {})
        now = datetime.now(UTC)
        violations: list[dict[str, object]] = []
        repaired = False
        check_types = _expanded_check_types(request.check_type)
        for check_type in check_types:
            if check_type == "stale_processing_leases":
                stale = self._stale_leases(now, request.limit)
                violations.extend(stale)
                if request.repair and stale:
                    repaired = self._lease_service.expire_old(now, request.limit) > 0 or repaired
            elif check_type == "outbox_stuck":
                violations.extend(self._stuck_outbox(now, request.limit))
            elif check_type == "inbox_failed":
                violations.extend(self._failed_inbox(request.limit))
            elif check_type == "commands_without_trace":
                violations.extend(self._commands_without_trace(request.limit))
            elif check_type == "kernel_boundary":
                violations.extend(self._kernel_boundary())
        if request.repair:
            expire = getattr(self._idempotency_service, "expire_old", None)
            if callable(expire):
                repaired = bool(expire(now=now, limit=request.limit)) or repaired

        status = "passed"
        if violations:
            status = "repaired" if repaired else "warning"
        result = ConsistencyCheckResult(
            consistency_check_id=f"consistency-{uuid4().hex}",
            trace_id=None,
            check_type=request.check_type,
            status=cast(ConsistencyCheckStatus, status),
            scope=request.scope,
            violations=violations,
            repaired=repaired,
            result={"violation_count": len(violations)},
            created_at=now,
            completed_at=datetime.now(UTC),
        )
        saved = self._repository.save_check(result)
        if violations:
            self._emit(
                "consistency_violation_detected",
                saved.consistency_check_id,
                0.9,
                {"violation_count": len(violations)},
            )
        self._emit(
            "consistency_check_completed",
            saved.consistency_check_id,
            0.7,
            {"status": saved.status},
        )
        return saved

    def _stale_leases(self, now: datetime, limit: int) -> list[dict[str, object]]:
        leases = self._repository.list_leases(status="active", limit=limit)
        return [
            {
                "type": "stale_processing_lease",
                "lease_id": lease.lease_id,
                "resource_type": lease.resource_type,
                "resource_id": lease.resource_id,
            }
            for lease in leases
            if lease.expires_at <= now
        ]

    def _stuck_outbox(self, now: datetime, limit: int) -> list[dict[str, object]]:
        if self._outbox_service is None:
            return []
        list_messages = getattr(self._outbox_service, "list_messages", None)
        if not callable(list_messages):
            return []
        threshold = now - timedelta(minutes=5)
        messages = list_messages(limit=limit)
        return [
            {"type": "stuck_outbox", "outbox_id": message.outbox_id, "status": message.status}
            for message in messages
            if message.status in {"pending", "sending"}
            and message.created_at is not None
            and message.created_at <= threshold
        ]

    def _failed_inbox(self, limit: int) -> list[dict[str, object]]:
        if self._inbox_service is None:
            return []
        list_messages = getattr(self._inbox_service, "list_messages", None)
        if not callable(list_messages):
            return []
        return [
            {"type": "failed_inbox", "inbox_id": message.inbox_id}
            for message in list_messages(status="failed", limit=limit)
        ]

    def _commands_without_trace(self, limit: int) -> list[dict[str, object]]:
        if self._command_repository is None:
            return []
        list_commands = getattr(self._command_repository, "list", None)
        if not callable(list_commands):
            return []
        return [
            {"type": "command_without_trace", "command_id": command.command_id}
            for command in list_commands(limit=limit)
            if command.trace_id is None
        ]

    def _kernel_boundary(self) -> list[dict[str, object]]:
        if self._boundary_checker is None:
            return []
        run = getattr(self._boundary_checker, "run", None)
        if not callable(run):
            return []
        try:
            findings = run()
        except Exception:
            return [{"type": "kernel_boundary", "reason": "boundary_checker_failed"}]
        return [{"type": "kernel_boundary", "finding": str(item)} for item in findings]

    def _emit(
        self,
        event_type: str,
        node_id: str,
        intensity: float,
        payload: dict[str, object],
    ) -> None:
        if self._telemetry_service is None:
            return
        event = VisualTelemetryEvent(
            telemetry_id=f"telemetry-{event_type}-{node_id}",
            trace_id=node_id,
            event_type=cast(VisualTelemetryEventType, event_type),
            node_type="consistency",
            node_id=node_id,
            edge_from=None,
            edge_to=node_id,
            intensity=intensity,
            payload=payload,
            created_at=datetime.now(UTC),
        )
        try:
            emit = getattr(self._telemetry_service, "emit", None)
            if callable(emit):
                emit(event)
        except Exception:
            return


def _expanded_check_types(check_type: str) -> list[str]:
    if check_type != "all":
        return [check_type]
    return [
        "commands_without_trace",
        "outbox_stuck",
        "inbox_failed",
        "duplicate_idempotency",
        "orphan_reaction_actions",
        "orphan_workflow_steps",
        "pending_approvals_expired",
        "stale_processing_leases",
        "kernel_boundary",
    ]
