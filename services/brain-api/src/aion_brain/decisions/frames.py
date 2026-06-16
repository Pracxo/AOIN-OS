"""Decision frame service."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from aion_brain.contracts.decisions import DecisionFrame, DecisionFrameCreateRequest
from aion_brain.decisions._shared import (
    audit_optional,
    authorize,
    emit_telemetry,
    provenance_optional,
    scope_matches,
)
from aion_brain.decisions.repository import DecisionRepository


class DecisionFrameService:
    """Create, read, list, and close decision frames."""

    def __init__(
        self,
        repository: DecisionRepository,
        policy_adapter: object,
        *,
        telemetry_service: object | None = None,
        audit_sink: object | None = None,
        provenance_service: object | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._telemetry_service = telemetry_service
        self._audit_sink = audit_sink
        self._provenance_service = provenance_service

    def create_frame(self, request: DecisionFrameCreateRequest) -> DecisionFrame:
        authorize(
            self._policy_adapter,
            action_type="decision.frame.create",
            resource_type="decision_frame",
            resource_id=request.decision_frame_id,
            scope=request.owner_scope,
            trace_id=request.trace_id,
            actor_id=request.actor_id,
            workspace_id=request.workspace_id,
            risk_level="low",
            context={"frame_type": request.frame_type},
        )
        now = datetime.now(UTC)
        frame = DecisionFrame(
            decision_frame_id=request.decision_frame_id or f"decision-frame-{uuid4().hex}",
            trace_id=request.trace_id,
            actor_id=request.actor_id,
            workspace_id=request.workspace_id,
            status="open",
            frame_type=request.frame_type,
            title=request.title,
            question=request.question,
            owner_scope=request.owner_scope,
            situation_refs=request.situation_refs,
            belief_refs=request.belief_refs,
            evidence_refs=request.evidence_refs,
            memory_refs=request.memory_refs,
            goal_refs=request.goal_refs,
            task_refs=request.task_refs,
            constraints=request.constraints,
            assumptions=request.assumptions,
            metadata=request.metadata,
            created_by=request.created_by,
            created_at=now,
            updated_at=now,
        )
        stored = self._repository.save_frame(frame)
        audit_optional(
            self._audit_sink,
            "decision_frame_created",
            {"decision_frame_id": stored.decision_frame_id, "frame_type": stored.frame_type},
        )
        for ref in stored.situation_refs:
            provenance_optional(self._provenance_service, stored.decision_frame_id, ref, "frames")
        for ref in stored.belief_refs:
            provenance_optional(
                self._provenance_service,
                stored.decision_frame_id,
                ref,
                "uses_belief",
            )
        emit_telemetry(
            self._telemetry_service,
            event_type="decision_frame_created",
            node_type="decision_frame",
            node_id=stored.decision_frame_id,
            intensity=0.5,
            trace_id=stored.trace_id,
            payload={"owner_scope": stored.owner_scope, "frame_type": stored.frame_type},
        )
        return stored

    def get_frame(self, decision_frame_id: str, scope: list[str]) -> DecisionFrame | None:
        authorize(
            self._policy_adapter,
            action_type="decision.frame.read",
            resource_type="decision_frame",
            resource_id=decision_frame_id,
            scope=scope,
        )
        frame = self._repository.get_frame(decision_frame_id)
        if frame is None or not scope_matches(frame.owner_scope, scope):
            return None
        return frame

    def list_frames(
        self,
        scope: list[str],
        status: str | None = None,
        frame_type: str | None = None,
        limit: int = 50,
    ) -> list[DecisionFrame]:
        authorize(
            self._policy_adapter,
            action_type="decision.frame.read",
            resource_type="decision_frame",
            resource_id=None,
            scope=scope,
        )
        return self._repository.list_frames(
            scope=scope,
            status=status,
            frame_type=frame_type,
            limit=limit,
        )

    def close_frame(
        self,
        decision_frame_id: str,
        actor_id: str | None,
        reason: str,
        scope: list[str],
    ) -> DecisionFrame:
        frame = self.get_frame(decision_frame_id, scope)
        if frame is None:
            raise ValueError("decision_frame_not_found")
        authorize(
            self._policy_adapter,
            action_type="decision.frame.update",
            resource_type="decision_frame",
            resource_id=decision_frame_id,
            scope=scope,
            actor_id=actor_id,
            trace_id=frame.trace_id,
            risk_level="low",
            context={"reason": reason},
        )
        closed = frame.model_copy(
            update={
                "status": "closed",
                "closed_at": datetime.now(UTC),
                "updated_at": datetime.now(UTC),
                "metadata": {**frame.metadata, "close_reason": reason},
            }
        )
        stored = self._repository.save_frame(closed)
        emit_telemetry(
            self._telemetry_service,
            event_type="decision_frame_closed",
            node_type="decision_frame",
            node_id=stored.decision_frame_id,
            intensity=0.4,
            trace_id=stored.trace_id,
            payload={"owner_scope": stored.owner_scope, "reason": reason},
        )
        return stored
