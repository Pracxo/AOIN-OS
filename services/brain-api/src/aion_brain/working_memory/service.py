"""Working memory stack service."""

from datetime import UTC, datetime, timedelta
from typing import Any, cast
from uuid import uuid4

from aion_brain.config import Settings
from aion_brain.contracts.policy import PolicyRequest
from aion_brain.contracts.telemetry import (
    VisualTelemetryEvent,
    VisualTelemetryEventType,
)
from aion_brain.contracts.working_memory import (
    WorkingMemoryQuery,
    WorkingMemorySlot,
    WorkingMemoryWriteRequest,
)
from aion_brain.policy.base import PolicyAdapter
from aion_brain.working_memory.repository import WorkingMemoryRepository


class WorkingMemoryService:
    """Manage short-lived working memory slots."""

    def __init__(
        self,
        repository: WorkingMemoryRepository,
        policy_adapter: PolicyAdapter,
        *,
        settings: Settings | None = None,
        telemetry_service: object | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._settings = settings
        self._telemetry_service = telemetry_service

    def write_slot(self, request: WorkingMemoryWriteRequest) -> WorkingMemorySlot:
        """Write one working memory slot."""
        self._authorize(
            action_type="working_memory.write",
            trace_id=request.trace_id,
            actor_id=request.actor_id,
            workspace_id=request.workspace_id,
            scope=request.owner_scope,
            resource_id=request.slot_id,
            context={"slot_type": request.slot_type, "source_type": request.source_type},
        )
        now = datetime.now(UTC)
        ttl_seconds = request.ttl_seconds
        if ttl_seconds is None and not request.pinned:
            ttl_seconds = _default_ttl_seconds(self._settings)
        expires_at = (
            None
            if request.pinned or ttl_seconds is None
            else now + timedelta(seconds=ttl_seconds)
        )
        slot = WorkingMemorySlot(
            slot_id=request.slot_id or f"wm-{uuid4().hex}",
            focus_session_id=request.focus_session_id,
            trace_id=request.trace_id,
            actor_id=request.actor_id,
            workspace_id=request.workspace_id,
            slot_type=request.slot_type,
            source_type=request.source_type,
            source_id=request.source_id,
            content=request.content,
            summary=request.summary,
            priority=request.priority,
            confidence=request.confidence,
            ttl_seconds=ttl_seconds,
            expires_at=expires_at,
            pinned=request.pinned,
            owner_scope=request.owner_scope,
            metadata=request.metadata,
            created_at=now,
            updated_at=now,
            deleted_at=None,
        )
        stored = self._repository.save(slot)
        self._emit_slot("working_memory_slot_written", stored, stored.priority)
        return stored

    def get_slot(self, slot_id: str, scope: list[str]) -> WorkingMemorySlot | None:
        """Return one visible slot."""
        self._authorize(
            action_type="working_memory.read",
            trace_id=None,
            actor_id=None,
            workspace_id=None,
            scope=scope,
            resource_id=slot_id,
            context={},
        )
        slot = self._repository.get(slot_id)
        if (
            slot is None
            or slot.deleted_at is not None
            or not _scope_matches(slot.owner_scope, scope)
        ):
            return None
        return slot

    def query_slots(self, query: WorkingMemoryQuery) -> list[WorkingMemorySlot]:
        """Query visible working memory slots."""
        self._authorize(
            action_type="working_memory.read",
            trace_id=None,
            actor_id=None,
            workspace_id=None,
            scope=query.scope,
            resource_id=query.focus_session_id,
            context={"operation": "query_working_memory"},
        )
        return self._repository.list_slots(
            scope=query.scope,
            focus_session_id=query.focus_session_id,
            slot_types=list(query.slot_types),
            source_types=list(query.source_types),
            include_expired=query.include_expired,
            pinned_only=query.pinned_only,
            limit=query.limit,
        )

    def pin_slot(self, slot_id: str, scope: list[str]) -> WorkingMemorySlot:
        """Pin a slot so TTL expiry does not hide it."""
        slot = self._require_slot(slot_id, scope)
        self._authorize_write_for_slot(slot, scope)
        stored = self._repository.save(
            slot.model_copy(
                update={
                    "pinned": True,
                    "expires_at": None,
                    "updated_at": datetime.now(UTC),
                }
            )
        )
        self._emit_slot("working_memory_slot_pinned", stored, stored.priority)
        return stored

    def unpin_slot(self, slot_id: str, scope: list[str]) -> WorkingMemorySlot:
        """Unpin a slot and restore default TTL."""
        slot = self._require_slot(slot_id, scope)
        self._authorize_write_for_slot(slot, scope)
        now = datetime.now(UTC)
        ttl_seconds = slot.ttl_seconds or _default_ttl_seconds(self._settings)
        stored = self._repository.save(
            slot.model_copy(
                update={
                    "pinned": False,
                    "ttl_seconds": ttl_seconds,
                    "expires_at": now + timedelta(seconds=ttl_seconds),
                    "updated_at": now,
                }
            )
        )
        return stored

    def delete_slot(self, slot_id: str, scope: list[str]) -> bool:
        """Soft-delete one visible slot."""
        slot = self._require_slot(slot_id, scope)
        self._authorize(
            action_type="working_memory.delete",
            trace_id=slot.trace_id,
            actor_id=slot.actor_id,
            workspace_id=slot.workspace_id,
            scope=scope,
            resource_id=slot.slot_id,
            context={"slot_type": slot.slot_type},
        )
        now = datetime.now(UTC)
        deleted = self._repository.save(
            slot.model_copy(update={"deleted_at": now, "updated_at": now})
        )
        self._emit_slot("working_memory_slot_deleted", deleted, 0.2)
        return True

    def sweep_expired(self, scope: list[str], limit: int = 100) -> dict[str, Any]:
        """Soft-delete expired unpinned slots."""
        self._authorize(
            action_type="working_memory.delete",
            trace_id=None,
            actor_id=None,
            workspace_id=None,
            scope=scope,
            resource_id=None,
            context={"operation": "sweep_expired"},
        )
        swept = self._repository.sweep_expired(scope=scope, limit=limit)
        event_id = f"working-memory-sweep-{uuid4().hex}"
        self._emit_generic(
            event_type="working_memory_expired_swept",
            node_id=event_id,
            trace_id=event_id,
            intensity=min(1.0, len(swept) / max(1, limit)),
            payload={"swept": len(swept), "owner_scope": scope},
        )
        return {"swept": len(swept), "slot_ids": [slot.slot_id for slot in swept]}

    def _require_slot(self, slot_id: str, scope: list[str]) -> WorkingMemorySlot:
        slot = self.get_slot(slot_id, scope)
        if slot is None:
            raise ValueError("working_memory_slot_not_found")
        return slot

    def _authorize_write_for_slot(self, slot: WorkingMemorySlot, scope: list[str]) -> None:
        self._authorize(
            action_type="working_memory.write",
            trace_id=slot.trace_id,
            actor_id=slot.actor_id,
            workspace_id=slot.workspace_id,
            scope=scope,
            resource_id=slot.slot_id,
            context={"slot_type": slot.slot_type},
        )

    def _authorize(
        self,
        *,
        action_type: str,
        trace_id: str | None,
        actor_id: str | None,
        workspace_id: str | None,
        scope: list[str],
        resource_id: str | None,
        context: dict[str, object],
    ) -> None:
        decision = self._policy_adapter.authorize(
            PolicyRequest(
                request_id=f"{action_type}-{resource_id or uuid4().hex}",
                trace_id=trace_id,
                actor_id=actor_id,
                workspace_id=workspace_id,
                action_type=action_type,
                resource_type="working_memory",
                resource_id=resource_id,
                risk_level="low",
                approval_present=False,
                requested_permissions=[],
                security_scope=scope,
                context=context,
            )
        )
        if not decision.allow:
            raise PermissionError(decision.reason)

    def _emit_slot(self, event_type: str, slot: WorkingMemorySlot, intensity: float) -> None:
        self._emit_generic(
            event_type=event_type,
            node_id=slot.slot_id,
            trace_id=slot.trace_id or slot.slot_id,
            intensity=intensity,
            payload={
                "slot_id": slot.slot_id,
                "slot_type": slot.slot_type,
                "source_type": slot.source_type,
                "owner_scope": slot.owner_scope,
                "workspace_id": slot.workspace_id,
                "priority": slot.priority,
            },
        )

    def _emit_generic(
        self,
        *,
        event_type: str,
        node_id: str,
        trace_id: str,
        intensity: float,
        payload: dict[str, object],
    ) -> None:
        if self._telemetry_service is None:
            return
        event = VisualTelemetryEvent(
            telemetry_id=f"telemetry-{trace_id}-{event_type}-{node_id}",
            trace_id=trace_id,
            event_type=cast(VisualTelemetryEventType, event_type),
            node_type="working_memory",
            node_id=node_id,
            edge_from=None,
            edge_to=None,
            intensity=max(0.0, min(1.0, intensity)),
            payload=payload,
            created_at=datetime.now(UTC),
        )
        _emit(self._telemetry_service, event)


def _default_ttl_seconds(settings: Settings | None) -> int:
    return int(getattr(settings, "working_memory_default_ttl_seconds", 3600))


def _scope_matches(owner_scope: list[str], requested_scope: list[str]) -> bool:
    return bool(set(owner_scope) & set(requested_scope))


def _emit(telemetry_service: object, event: VisualTelemetryEvent) -> None:
    try:
        emit = getattr(telemetry_service, "emit", None)
        if callable(emit):
            emit(event)
            return
        save = getattr(telemetry_service, "save_visual_telemetry", None)
        if callable(save):
            save(event.trace_id, [event])
    except Exception:
        return
