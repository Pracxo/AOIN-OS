"""Operator Action Center service."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, cast
from uuid import uuid4

from aion_brain.contracts.operator import (
    OperatorAcknowledgement,
    OperatorAcknowledgementRequest,
    OperatorActionItem,
    OperatorSeverity,
)
from aion_brain.contracts.policy import PolicyRequest
from aion_brain.contracts.telemetry import VisualTelemetryEvent
from aion_brain.operator.repository import OperatorRepository

_FAILED_STATUSES = {"failed", "error", "critical"}
_OPEN_CIRCUIT_STATUSES = {"open", "half_open"}
_PENDING_APPROVAL_STATUSES = {"pending"}


class ActionCenterService:
    """Build generic local operator action items without executing actions."""

    def __init__(
        self,
        repository: OperatorRepository,
        policy_adapter: object | None = None,
        telemetry_service: object | None = None,
        **sources: object,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._telemetry_service = telemetry_service
        self._sources = sources

    def build_action_items(self, scope: list[str], limit: int = 100) -> list[OperatorActionItem]:
        """Build and persist action recommendations from read-only local state."""
        self._authorize("operator.actions.read", scope, "operator_action_items", None)
        generated: list[OperatorActionItem] = []
        generated.extend(self._pending_approval_items(scope))
        generated.extend(self._failed_command_items())
        generated.extend(self._open_circuit_breaker_items())
        generated.extend(self._failed_audit_verification_items())
        stored: list[OperatorActionItem] = []
        for item in generated[:limit]:
            saved = self._repository.save_action_item(item)
            stored.append(saved)
            if saved.action_item_id == item.action_item_id and saved.created_at == item.created_at:
                self._emit_action_created(saved)
        existing = self._repository.list_action_items(status="open", limit=limit)
        by_id = {item.action_item_id: item for item in [*stored, *existing]}
        return list(by_id.values())[:limit]

    def acknowledge(
        self,
        request: OperatorAcknowledgementRequest,
    ) -> OperatorAcknowledgement:
        """Record acknowledgement without resolving or mutating the source issue."""
        self._authorize(
            "operator.acknowledgement.create",
            ["workspace:main"],
            request.source_type,
            request.source_id,
        )
        acknowledgement = OperatorAcknowledgement(
            acknowledgement_id=request.acknowledgement_id or f"ack-{uuid4().hex}",
            action_item_id=request.action_item_id,
            source_type=request.source_type,
            source_id=request.source_id,
            actor_id=request.actor_id,
            workspace_id=request.workspace_id,
            reason=request.reason,
            metadata=request.metadata,
            created_at=datetime.now(UTC),
        )
        stored = self._repository.save_acknowledgement(acknowledgement)
        if request.action_item_id:
            self._repository.acknowledge_action_item(request.action_item_id)
        self._emit_acknowledged(stored)
        return stored

    def list_acknowledgements(
        self,
        source_type: str | None = None,
        source_id: str | None = None,
        limit: int = 100,
    ) -> list[OperatorAcknowledgement]:
        """List local acknowledgement records."""
        self._authorize(
            "operator.acknowledgement.read",
            ["workspace:main"],
            source_type or "operator_acknowledgement",
            source_id,
        )
        return self._repository.list_acknowledgements(
            source_type=source_type,
            source_id=source_id,
            limit=limit,
        )

    def _pending_approval_items(self, scope: list[str]) -> list[OperatorActionItem]:
        items = _list_from(
            self._sources.get("approval_service"),
            ("list_requests", "list"),
            scope,
        )
        return [
            _action_item(
                source_type="approval",
                source_id=_id_for(item, "approval_request_id"),
                trace_id=getattr(item, "trace_id", None),
                category="approvals",
                severity=_approval_severity(item),
                title="Pending approval requires review.",
                description="A local approval request is waiting for operator review.",
                recommended_action="review_pending_approval",
                runbook_ref="docs/operations/operator-control-tower.md",
                scope=_scope_for(item, scope, "approval_scope"),
                metadata={"status": getattr(item, "status", "pending")},
            )
            for item in items
            if str(getattr(item, "status", "")).lower() in _PENDING_APPROVAL_STATUSES
        ]

    def _failed_command_items(self) -> list[OperatorActionItem]:
        items = _list_from(self._sources.get("command_service"), ("list_commands", "list"), [])
        return [
            _action_item(
                source_type="command",
                source_id=_id_for(item, "command_id"),
                trace_id=getattr(item, "trace_id", None),
                category="commands",
                severity="high",
                title="Failed command requires inspection.",
                description="A local command ended in a failed state.",
                recommended_action="inspect_failed_command",
                runbook_ref="docs/operations/local-ops-runbook.md",
                scope=["workspace:main"],
                metadata={"status": getattr(item, "status", "failed")},
            )
            for item in items
            if str(getattr(item, "status", "")).lower() in _FAILED_STATUSES
        ]

    def _open_circuit_breaker_items(self) -> list[OperatorActionItem]:
        items = _list_from(
            self._sources.get("resilience_service"),
            ("list_circuit_breakers", "list"),
            [],
        )
        return [
            _action_item(
                source_type="resilience",
                source_id=_id_for(item, "name"),
                trace_id=None,
                category="resilience",
                severity="critical",
                title="Open circuit breaker requires inspection.",
                description="A local circuit breaker is open or half-open.",
                recommended_action="inspect_degraded_component",
                runbook_ref="docs/operations/resilience.md",
                scope=["workspace:main"],
                metadata={"status": getattr(item, "status", "open")},
            )
            for item in items
            if str(getattr(item, "status", "")).lower() in _OPEN_CIRCUIT_STATUSES
        ]

    def _failed_audit_verification_items(self) -> list[OperatorActionItem]:
        source = self._sources.get("audit_service")
        latest = _call_optional(source, ("latest_verification_run", "latest_verification"))
        if latest is None:
            return []
        if str(getattr(latest, "status", "")).lower() not in _FAILED_STATUSES:
            return []
        return [
            _action_item(
                source_type="audit",
                source_id=_id_for(latest, "audit_verification_id"),
                trace_id=getattr(latest, "trace_id", None),
                category="audit",
                severity="critical",
                title="Audit verification failed.",
                description="A local audit integrity verification reported a failure.",
                recommended_action="run_audit_verification",
                runbook_ref="docs/operations/audit-integrity.md",
                scope=["workspace:main"],
                metadata={"status": getattr(latest, "status", "failed")},
            )
        ]

    def _authorize(
        self,
        action_type: str,
        scope: list[str],
        resource_type: str,
        resource_id: str | None,
    ) -> None:
        authorize = getattr(self._policy_adapter, "authorize", None)
        if not callable(authorize):
            return
        decision = authorize(
            PolicyRequest(
                request_id=f"operator-{uuid4().hex}",
                trace_id=None,
                actor_id=None,
                workspace_id=None,
                action_type=action_type,
                resource_type=resource_type,
                resource_id=resource_id,
                risk_level="low",
                approval_present=False,
                requested_permissions=[action_type],
                security_scope=scope,
                context={"source": "operator_action_center"},
            )
        )
        if not decision.allow:
            raise PermissionError(decision.reason)

    def _emit_action_created(self, item: OperatorActionItem) -> None:
        _emit(
            self._telemetry_service,
            "operator_action_item_created",
            "action_item",
            item.action_item_id,
            _intensity_for(item.severity),
            {"severity": item.severity, "source_type": item.source_type},
            item.trace_id,
        )

    def _emit_acknowledged(self, acknowledgement: OperatorAcknowledgement) -> None:
        _emit(
            self._telemetry_service,
            "operator_action_acknowledged",
            "action_item",
            acknowledgement.action_item_id or acknowledgement.source_id,
            0.3,
            {"source_type": acknowledgement.source_type},
            None,
        )


def _action_item(
    *,
    source_type: str,
    source_id: str,
    trace_id: str | None,
    category: str,
    severity: OperatorSeverity,
    title: str,
    description: str,
    recommended_action: str,
    runbook_ref: str,
    scope: list[str],
    metadata: dict[str, Any],
) -> OperatorActionItem:
    return OperatorActionItem(
        action_item_id=f"action-{source_type}-{source_id}",
        trace_id=trace_id,
        source_type=cast(Any, source_type),
        source_id=source_id,
        category=cast(Any, category),
        severity=severity,
        status="open",
        title=title,
        description=description,
        recommended_action=recommended_action,
        runbook_ref=runbook_ref,
        owner_scope=scope or ["workspace:main"],
        metadata=metadata,
        created_at=datetime.now(UTC),
    )


def _list_from(source: object | None, methods: tuple[str, ...], scope: list[str]) -> list[object]:
    if source is None:
        return []
    for name in methods:
        method = getattr(source, name, None)
        if callable(method):
            callable_method = cast(Any, method)
            if name == "list_requests":
                try:
                    from aion_brain.contracts.approvals import ApprovalInboxQuery

                    return list(
                        callable_method(
                            ApprovalInboxQuery(scope=scope or ["workspace:main"], limit=100)
                        )
                        or []
                    )
                except (ImportError, TypeError):
                    pass
            attempts: tuple[dict[str, object], ...] = (
                {"scope": scope, "limit": 100},
                {"scope": scope},
                {"status": None, "limit": 100},
                {"limit": 100},
                {},
            )
            for kwargs in attempts:
                try:
                    return list(callable_method(**kwargs) or [])
                except TypeError:
                    continue
    return []


def _call_optional(source: object | None, methods: tuple[str, ...]) -> object | None:
    if source is None:
        return None
    for name in methods:
        method = getattr(source, name, None)
        if callable(method):
            callable_method = cast(Any, method)
            return cast(object, callable_method())
    return None


def _id_for(item: object, attr: str) -> str:
    value = getattr(item, attr, None)
    if value is not None:
        return str(value)
    return uuid4().hex


def _scope_for(item: object, fallback: list[str], attr: str) -> list[str]:
    value = getattr(item, attr, None)
    if isinstance(value, list) and value:
        return [str(entry) for entry in value]
    return fallback or ["workspace:main"]


def _approval_severity(item: object) -> OperatorSeverity:
    priority = str(getattr(item, "priority", "")).lower()
    if priority in {"urgent"}:
        return "critical"
    if priority in {"high"}:
        return "high"
    return "medium"


def _intensity_for(severity: OperatorSeverity) -> float:
    if severity == "critical":
        return 1.0
    if severity == "high":
        return 0.7
    return 0.4


def _emit(
    telemetry_service: object | None,
    event_type: str,
    node_type: str,
    node_id: str,
    intensity: float,
    payload: dict[str, object],
    trace_id: str | None,
) -> None:
    emit = getattr(telemetry_service, "emit", None)
    if not callable(emit):
        return
    try:
        emit(
            VisualTelemetryEvent(
                telemetry_id=f"telemetry-operator-{event_type}-{node_id}-{uuid4().hex}",
                trace_id=trace_id or "operator",
                event_type=cast(Any, event_type),
                node_type=cast(Any, node_type),
                node_id=node_id,
                edge_from=None,
                edge_to=None,
                intensity=intensity,
                payload=payload,
                created_at=datetime.now(UTC),
            )
        )
    except Exception:
        return
