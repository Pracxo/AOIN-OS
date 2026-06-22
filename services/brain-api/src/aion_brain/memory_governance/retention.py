"""Memory retention sweep service."""

from datetime import UTC, datetime
from typing import Any, cast

from aion_brain.contracts.memory import MemoryRecord
from aion_brain.contracts.memory_governance import (
    MemoryGovernanceEvaluationRequest,
    MemoryRetentionSweepRequest,
    MemoryRetentionSweepResult,
)
from aion_brain.contracts.policy import PolicyRequest
from aion_brain.contracts.telemetry import VisualTelemetryEvent
from aion_brain.memory_governance.decay import MemoryDecayService
from aion_brain.memory_governance.engine import MemoryGovernanceEngine
from aion_brain.policy.base import PolicyAdapter


class MemoryRetentionService:
    """Apply retention and decay governance without hard deletes."""

    def __init__(
        self,
        *,
        memory_service: object,
        governance_engine: MemoryGovernanceEngine,
        decay_service: MemoryDecayService,
        policy_adapter: PolicyAdapter,
        telemetry_service: object | None,
    ) -> None:
        self._memory_service = memory_service
        self._governance_engine = governance_engine
        self._decay_service = decay_service
        self._policy_adapter = policy_adapter
        self._telemetry_service = telemetry_service

    def sweep(self, request: MemoryRetentionSweepRequest) -> MemoryRetentionSweepResult:
        """Run a policy-gated retention sweep."""
        decision = self._policy_adapter.authorize(
            PolicyRequest(
                request_id="memory.retention.sweep",
                trace_id=None,
                actor_id=None,
                workspace_id=None,
                action_type="memory.retention.sweep",
                resource_type="memory",
                resource_id=None,
                risk_level="medium" if not request.dry_run else "low",
                approval_present=request.approval_present,
                requested_permissions=[],
                security_scope=request.owner_scope,
                context=request.model_dump(mode="json"),
            )
        )
        if not decision.allow:
            return MemoryRetentionSweepResult(
                evaluated=0,
                expired=0,
                decayed=0,
                pending_approval=0,
                skipped=0,
                dry_run=request.dry_run,
                decisions=[],
            )
        list_active = getattr(self._memory_service, "list_active", None)
        if not callable(list_active):
            return MemoryRetentionSweepResult(
                evaluated=0,
                expired=0,
                decayed=0,
                pending_approval=0,
                skipped=0,
                dry_run=request.dry_run,
                decisions=[],
            )
        records = list_active(
            request.owner_scope,
            limit=request.limit,
            memory_types=cast(Any, request.memory_types or None),
        )
        governance_decisions = []
        expired = 0
        decayed = 0
        pending = 0
        for memory in records:
            if not isinstance(memory, MemoryRecord):
                continue
            governance = self._governance_engine.evaluate(
                MemoryGovernanceEvaluationRequest(
                    trace_id=None,
                    memory=memory,
                    action_type="memory.decay",
                    owner_scope=request.owner_scope,
                    context={"approval_present": request.approval_present},
                )
            )
            governance_decisions.append(governance)
            if governance.decision == "expire":
                expired += 1
                if not request.dry_run:
                    expire = getattr(self._memory_service, "expire", None)
                    if callable(expire) and bool(expire(memory.memory_id)):
                        continue
                    update_metadata = getattr(self._memory_service, "update_metadata", None)
                    if callable(update_metadata):
                        update_metadata(
                            memory.memory_id,
                            {**memory.metadata, "governance_status": "expired"},
                        )
            elif governance.decision == "decay":
                decayed += 1
                if not request.dry_run:
                    self._decay_service.decay_memory(memory.memory_id, "retention_sweep")
            elif governance.decision in {"require_approval", "forget"}:
                pending += 1
        result = MemoryRetentionSweepResult(
            evaluated=len(records),
            expired=expired,
            decayed=decayed,
            pending_approval=pending,
            skipped=max(0, len(records) - expired - decayed - pending),
            dry_run=request.dry_run,
            decisions=governance_decisions,
        )
        self._emit("memory_retention_sweep_completed", "retention", 0.6, result.model_dump())
        return result

    def _emit(
        self,
        event_type: str,
        node_id: str,
        intensity: float,
        payload: dict[str, Any],
    ) -> None:
        if self._telemetry_service is None:
            return
        event = VisualTelemetryEvent(
            telemetry_id=f"telemetry-{node_id}-{event_type}",
            trace_id=node_id,
            event_type=cast(Any, event_type),
            node_type="retention",
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
