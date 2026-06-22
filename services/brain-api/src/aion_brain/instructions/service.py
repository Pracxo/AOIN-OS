"""Policy-gated instruction record service."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, cast
from uuid import uuid4

from aion_brain.audit_integrity.ledger import record_audit_event
from aion_brain.contracts.instructions import InstructionConflict, InstructionRecord
from aion_brain.contracts.policy import PolicyDecision, PolicyRequest
from aion_brain.contracts.telemetry import (
    VisualNodeType,
    VisualTelemetryEvent,
    VisualTelemetryEventType,
)
from aion_brain.instructions.normalizer import (
    detect_forbidden_override_attempt,
    normalize_instruction_text,
)
from aion_brain.instructions.repository import InstructionRepository


class InstructionService:
    """Create and manage normalized instruction records."""

    def __init__(
        self,
        repository: InstructionRepository,
        policy_adapter: object | None,
        *,
        conflict_detector: object | None = None,
        telemetry_service: object | None = None,
        audit_sink: object | None = None,
        settings: object | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._conflict_detector = conflict_detector
        self._telemetry_service = telemetry_service
        self._audit_sink = audit_sink
        self._settings = settings

    def set_conflict_detector(self, conflict_detector: object | None) -> None:
        """Attach conflict detector after service graph assembly."""

        self._conflict_detector = conflict_detector

    def create_instruction(self, instruction: InstructionRecord) -> InstructionRecord:
        """Create one instruction after policy authorization."""

        _ensure_enabled(self._settings, "instructions_enabled", "instructions_disabled")
        _authorize(
            self._policy_adapter,
            "instruction.create",
            "instruction",
            instruction.instruction_id,
            instruction.owner_scope,
            trace_id=instruction.trace_id,
            actor_id=instruction.actor_id,
            workspace_id=instruction.workspace_id,
            risk_level="low",
            context={"instruction_type": instruction.instruction_type},
        )
        normalized = instruction.normalized_instruction or normalize_instruction_text(
            instruction.instruction_text
        )
        stored = self._repository.save_instruction(
            instruction.model_copy(
                update={
                    "normalized_instruction": normalized,
                    "created_at": instruction.created_at or datetime.now(UTC),
                    "updated_at": datetime.now(UTC),
                }
            )
        )
        if detect_forbidden_override_attempt(stored.instruction_text):
            self._create_override_conflict(stored)
        _emit(
            self._telemetry_service,
            event_type="instruction_created",
            node_type="instruction",
            node_id=stored.instruction_id,
            trace_id=stored.trace_id,
            intensity=0.7,
            payload={
                "owner_scope": stored.owner_scope,
                "instruction_type": stored.instruction_type,
            },
        )
        record_audit_event(
            self._audit_sink,
            action_type="instruction.create",
            resource_type="instruction",
            resource_id=stored.instruction_id,
            event_type="instruction_created",
            outcome="completed",
            source_component="instruction_service",
            trace_id=stored.trace_id,
            actor_id=stored.actor_id,
            workspace_id=stored.workspace_id,
            payload={"instruction_type": stored.instruction_type, "scope_type": stored.scope_type},
        )
        return stored

    def get_instruction(self, instruction_id: str, scope: list[str]) -> InstructionRecord | None:
        """Return one instruction if visible to scope."""

        _authorize(
            self._policy_adapter,
            "instruction.read",
            "instruction",
            instruction_id,
            scope,
        )
        record = self._repository.get_instruction(instruction_id)
        if record is None or not _scope_matches(record.owner_scope, scope):
            return None
        return record

    def list_instructions(
        self,
        scope: list[str],
        *,
        status: str | None = None,
        instruction_type: str | None = None,
        scope_type: str | None = None,
        limit: int = 100,
    ) -> list[InstructionRecord]:
        """List instructions visible to a scope."""

        _authorize(self._policy_adapter, "instruction.read", "instruction", None, scope)
        return self._repository.list_instructions(
            scope=scope,
            status=status,
            instruction_type=instruction_type,
            scope_type=scope_type,
            limit=limit,
        )

    def disable_instruction(
        self,
        instruction_id: str,
        *,
        actor_id: str | None = None,
        reason: str | None = None,
    ) -> InstructionRecord:
        """Disable one instruction."""

        record = self._repository.get_instruction(instruction_id)
        if record is None:
            raise ValueError("instruction_not_found")
        _authorize(
            self._policy_adapter,
            "instruction.update",
            "instruction",
            instruction_id,
            record.owner_scope,
            actor_id=actor_id,
            risk_level="low",
            context={"reason": reason},
        )
        now = datetime.now(UTC)
        stored = self._repository.save_instruction(
            record.model_copy(
                update={
                    "status": "disabled",
                    "disabled_at": now,
                    "updated_at": now,
                    "metadata": {**record.metadata, "disabled_reason": reason},
                }
            )
        )
        _emit(
            self._telemetry_service,
            event_type="instruction_disabled",
            node_type="instruction",
            node_id=stored.instruction_id,
            trace_id=stored.trace_id,
            intensity=0.5,
            payload={"reason": reason, "owner_scope": stored.owner_scope},
        )
        return stored

    def expire_old(self, now: datetime | None = None) -> list[InstructionRecord]:
        """Mark active expired instructions as expired."""

        current = now or datetime.now(UTC)
        expired: list[InstructionRecord] = []
        for record in self._repository.list_instructions(status="active", limit=5000):
            if record.expires_at is not None and record.expires_at <= current:
                expired.append(
                    self._repository.save_instruction(
                        record.model_copy(update={"status": "expired", "updated_at": current})
                    )
                )
        return expired

    def _create_override_conflict(self, instruction: InstructionRecord) -> None:
        create_conflict = getattr(self._conflict_detector, "create_conflict", None)
        if not callable(create_conflict):
            return
        try:
            create_conflict(
                InstructionConflict(
                    conflict_id=f"instruction-conflict-{uuid4().hex}",
                    trace_id=instruction.trace_id,
                    actor_id=instruction.actor_id,
                    workspace_id=instruction.workspace_id,
                    conflict_type="policy_override_attempt",
                    severity="critical",
                    status="open",
                    owner_scope=instruction.owner_scope,
                    instruction_ids=[instruction.instruction_id],
                    reason="Instruction attempts to override a hard AION boundary.",
                    metadata={"source": "instruction_service"},
                    created_by=instruction.created_by,
                )
            )
        except Exception:
            return


def _authorize(
    policy_adapter: object | None,
    action_type: str,
    resource_type: str,
    resource_id: str | None,
    scope: list[str],
    *,
    trace_id: str | None = None,
    actor_id: str | None = None,
    workspace_id: str | None = None,
    risk_level: str = "low",
    context: dict[str, Any] | None = None,
) -> PolicyDecision:
    authorize = getattr(policy_adapter, "authorize", None)
    if not callable(authorize):
        raise PermissionError("policy_adapter_unavailable")
    decision = authorize(
        PolicyRequest(
            request_id=f"{action_type}-{resource_id or uuid4().hex}",
            trace_id=trace_id,
            actor_id=actor_id,
            workspace_id=workspace_id,
            action_type=action_type,
            resource_type=resource_type,
            resource_id=resource_id,
            risk_level=risk_level,
            approval_present=False,
            requested_permissions=[action_type],
            security_scope=scope,
            context=context or {},
        )
    )
    if not isinstance(decision, PolicyDecision):
        raise TypeError("policy adapter returned a non-PolicyDecision value")
    if not decision.allow:
        raise PermissionError(decision.reason)
    return decision


def _emit(
    telemetry_service: object | None,
    *,
    event_type: str,
    node_type: str,
    node_id: str,
    trace_id: str | None,
    intensity: float,
    payload: dict[str, object],
) -> None:
    emit = getattr(telemetry_service, "emit", None)
    if not callable(emit):
        return
    try:
        emit(
            VisualTelemetryEvent(
                telemetry_id=f"telemetry-{event_type}-{node_id}-{uuid4().hex}",
                trace_id=trace_id or node_id,
                event_type=cast(VisualTelemetryEventType, event_type),
                node_type=cast(VisualNodeType, node_type),
                node_id=node_id,
                edge_from=None,
                edge_to=None,
                intensity=max(0.0, min(1.0, intensity)),
                payload=payload,
                created_at=datetime.now(UTC),
            )
        )
    except Exception:
        return


def _scope_matches(owner_scope: list[str], scope: list[str]) -> bool:
    return bool(set(owner_scope).intersection(scope))


def _ensure_enabled(settings: object | None, field: str, reason: str) -> None:
    if settings is not None and not bool(getattr(settings, field, True)):
        raise RuntimeError(reason)


__all__ = ["InstructionService", "_authorize", "_emit", "_ensure_enabled", "_scope_matches"]
