"""Deterministic memory decay scoring."""

from datetime import UTC, datetime
from typing import Any, cast
from uuid import uuid4

from aion_brain.config import Settings
from aion_brain.contracts.memory import MemoryRecord
from aion_brain.contracts.memory_governance import MemoryDecayRecord, MemoryRetentionSweepResult
from aion_brain.contracts.telemetry import VisualTelemetryEvent
from aion_brain.memory_governance.repository import MemoryGovernanceRepository


class MemoryDecayService:
    """Compute and persist memory decay scores without deleting memory."""

    def __init__(
        self,
        *,
        governance_repository: MemoryGovernanceRepository,
        memory_service: object,
        telemetry_service: object | None,
        settings: Settings,
    ) -> None:
        self._repository = governance_repository
        self._memory_service = memory_service
        self._telemetry_service = telemetry_service
        self._settings = settings

    def compute_decay_score(
        self,
        memory: MemoryRecord,
        now: datetime | None = None,
    ) -> tuple[float, dict[str, Any]]:
        """Return a deterministic score and factor map."""
        current = now or datetime.now(UTC)
        created = (
            memory.created_at if memory.created_at.tzinfo else memory.created_at.replace(tzinfo=UTC)
        )
        age_days = max(0.0, (current - created).total_seconds() / 86400)
        half_life_days = max(1, self._settings.memory_default_decay_half_life_days)
        age_factor = 0.5 ** (age_days / half_life_days)
        score = memory.confidence * age_factor
        factors: dict[str, Any] = {
            "base_confidence": memory.confidence,
            "age_days": age_days,
            "half_life_days": half_life_days,
            "age_factor": age_factor,
        }
        if memory.confidence < self._settings.memory_low_confidence_threshold:
            score -= 0.05
            factors["low_confidence_penalty"] = 0.05
        if not memory.source_event_id:
            score -= 0.10
            factors["missing_source_event_id_penalty"] = 0.10
        if memory.memory_type in {"semantic", "procedural"} and not memory.content_ref:
            score -= 0.10
            factors["missing_content_ref_penalty"] = 0.10
        if memory.metadata.get("evidence_refs"):
            score += 0.10
            factors["evidence_ref_bonus"] = 0.10
        if memory.metadata.get("last_retrieved_at"):
            score += 0.05
            factors["recent_access_bonus"] = 0.05
        return _clamp(score), factors

    def decay_memory(self, memory_id: str, reason: str) -> MemoryDecayRecord:
        """Persist a decay record and annotate memory metadata when supported."""
        get = getattr(self._memory_service, "get", None)
        if not callable(get):
            raise ValueError("memory_service_get_unavailable")
        memory = get(memory_id)
        if not isinstance(memory, MemoryRecord):
            raise ValueError("memory_not_found")
        new_score, factors = self.compute_decay_score(memory)
        record = MemoryDecayRecord(
            decay_id=f"memory-decay-{uuid4().hex}",
            memory_id=memory.memory_id,
            previous_score=memory.confidence,
            new_score=new_score,
            decay_reason=reason,
            factors=factors,
            created_at=datetime.now(UTC),
        )
        saved = self._repository.save_decay_record(record)
        update_metadata = getattr(self._memory_service, "update_metadata", None)
        if callable(update_metadata):
            update_metadata(
                memory.memory_id,
                {
                    **memory.metadata,
                    "governance_decay_score": new_score,
                    "governance_decay_reason": reason,
                },
            )
        self._emit(
            "memory_decayed",
            memory.memory_id,
            new_score,
            {"decay_reason": reason, "factors": factors},
        )
        return saved

    def recompute_decay(
        self,
        scope: list[str],
        memory_types: list[str],
        limit: int,
        dry_run: bool,
    ) -> MemoryRetentionSweepResult:
        """Recompute decay scores for active memory records."""
        if not self._settings.memory_decay_enabled:
            return MemoryRetentionSweepResult(
                evaluated=0,
                expired=0,
                decayed=0,
                pending_approval=0,
                skipped=0,
                dry_run=dry_run,
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
                dry_run=dry_run,
                decisions=[],
            )
        records = list_active(scope, limit=limit, memory_types=cast(Any, memory_types or None))
        decayed = 0
        for memory in records:
            if not isinstance(memory, MemoryRecord):
                continue
            score, _ = self.compute_decay_score(memory)
            if score < memory.confidence:
                decayed += 1
                if not dry_run:
                    self.decay_memory(memory.memory_id, "retention_recompute")
        return MemoryRetentionSweepResult(
            evaluated=len(records),
            expired=0,
            decayed=decayed,
            pending_approval=0,
            skipped=max(0, len(records) - decayed),
            dry_run=dry_run,
            decisions=[],
        )

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
            node_type="memory",
            node_id=node_id,
            edge_from=None,
            edge_to=node_id,
            intensity=_clamp(intensity),
            payload=payload,
            created_at=datetime.now(UTC),
        )
        try:
            emit = getattr(self._telemetry_service, "emit", None)
            if callable(emit):
                emit(event)
                return
            save = getattr(self._telemetry_service, "save_visual_telemetry", None)
            if callable(save):
                save(event.trace_id, [event])
        except Exception:
            return


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))
