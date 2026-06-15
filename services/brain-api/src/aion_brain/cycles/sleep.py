"""Sleep consolidation coordination."""

from datetime import UTC, datetime
from typing import Any, cast
from uuid import uuid4

from aion_brain.contracts.cycles import CognitiveCycleRun, SleepConsolidationRecord
from aion_brain.contracts.memory_governance import (
    MemoryCompactionRequest,
    MemoryConflictScanRequest,
)
from aion_brain.contracts.telemetry import VisualTelemetryEvent


class SleepConsolidationService:
    """Coordinate deterministic sleep consolidation through existing services."""

    def __init__(
        self,
        *,
        working_memory_service: object | None = None,
        memory_decay_service: object | None = None,
        memory_conflict_service: object | None = None,
        memory_compaction_service: object | None = None,
        reflection_engine: object | None = None,
        skill_service: object | None = None,
        regression_service: object | None = None,
        replay_service: object | None = None,
        visual_service: object | None = None,
        observability_service: object | None = None,
        telemetry_service: object | None = None,
        cycle_repository: object | None = None,
        settings: object | None = None,
    ) -> None:
        self._working_memory_service = working_memory_service
        self._memory_decay_service = memory_decay_service
        self._memory_conflict_service = memory_conflict_service
        self._memory_compaction_service = memory_compaction_service
        self._reflection_engine = reflection_engine
        self._skill_service = skill_service
        self._regression_service = regression_service
        self._replay_service = replay_service
        self._visual_service = visual_service
        self._observability_service = observability_service
        self._telemetry_service = telemetry_service
        self._cycle_repository = cycle_repository
        self._settings = settings

    def run(self, cycle_run: CognitiveCycleRun, dry_run: bool) -> SleepConsolidationRecord:
        """Run deterministic consolidation and persist the summary record."""
        self._emit(
            "sleep_consolidation_started",
            "consolidation",
            cycle_run.cycle_run_id,
            0.6,
            {"cycle_run_id": cycle_run.cycle_run_id, "dry_run": dry_run},
            cycle_run.trace_id,
        )
        working_memory = self._sweep_working_memory(cycle_run, dry_run)
        decay = self._recompute_decay(cycle_run, dry_run)
        conflicts = self._scan_conflicts(cycle_run)
        compaction = self._compact_memory(cycle_run, dry_run)
        reflections_created = self._create_reflections(cycle_run, dry_run)
        skill_candidates_created = self._create_skill_candidates(cycle_run, dry_run)
        regression_checked = self._run_regression(cycle_run)
        visual_snapshots = self._create_visual_snapshot(cycle_run, dry_run)
        observability = self._observability_summary(cycle_run)

        record = SleepConsolidationRecord(
            consolidation_id=f"sleep-consolidation-{uuid4().hex}",
            cycle_run_id=cycle_run.cycle_run_id,
            trace_id=cycle_run.trace_id,
            actor_id=cycle_run.actor_id,
            workspace_id=cycle_run.workspace_id,
            owner_scope=cycle_run.owner_scope,
            working_memory_slots_reviewed=int(working_memory.get("count", 0)),
            memories_decayed=int(decay.get("decayed", 0)),
            conflicts_detected=int(conflicts.get("count", 0)),
            compaction_runs=int(compaction.get("runs", 0)),
            reflections_created=reflections_created,
            skill_candidates_created=skill_candidates_created,
            regression_cases_checked=regression_checked,
            visual_snapshots_created=visual_snapshots,
            summary="Sleep consolidation completed deterministically.",
            result={
                "dry_run": dry_run,
                "working_memory": working_memory,
                "memory_decay": decay,
                "memory_conflicts": conflicts,
                "memory_compaction": compaction,
                "observability": observability,
                "skill_promotion": "not_performed",
            },
            created_at=datetime.now(UTC),
        )
        save = getattr(self._cycle_repository, "save_sleep_record", None)
        saved = save(record) if callable(save) else record
        self._emit(
            "sleep_consolidation_completed",
            "consolidation",
            saved.consolidation_id,
            0.9,
            saved.model_dump(mode="json"),
            cycle_run.trace_id,
        )
        return saved

    def _sweep_working_memory(self, cycle_run: CognitiveCycleRun, dry_run: bool) -> dict[str, Any]:
        limit = int(
            cycle_run.input.get(
                "working_memory_sweep_limit",
                getattr(self._settings, "cycle_default_working_memory_sweep_limit", 100),
            )
        )
        if dry_run:
            count = _safe_call(
                self._working_memory_service,
                "count_expired",
                cycle_run.owner_scope,
                limit,
            )
            return {"dry_run": True, "count": int(count or 0), "mutated": False}
        result = _safe_call(
            self._working_memory_service,
            "sweep_expired",
            cycle_run.owner_scope,
            limit,
        )
        return {"dry_run": False, "count": int(_dict(result).get("swept", 0)), "mutated": True}

    def _recompute_decay(self, cycle_run: CognitiveCycleRun, dry_run: bool) -> dict[str, Any]:
        limit = int(
            cycle_run.input.get(
                "memory_decay_limit",
                getattr(self._settings, "cycle_default_memory_decay_limit", 500),
            )
        )
        result = _safe_call(
            self._memory_decay_service,
            "recompute_decay",
            cycle_run.owner_scope,
            [],
            limit,
            dry_run,
        )
        payload = _model_or_dict(result)
        return {"dry_run": dry_run, "decayed": int(payload.get("decayed", 0)), "result": payload}

    def _scan_conflicts(self, cycle_run: CognitiveCycleRun) -> dict[str, Any]:
        limit = int(
            cycle_run.input.get(
                "conflict_scan_limit",
                getattr(self._settings, "cycle_default_conflict_scan_limit", 500),
            )
        )
        result = _safe_call(
            self._memory_conflict_service,
            "scan",
            MemoryConflictScanRequest(owner_scope=cycle_run.owner_scope, limit=limit),
        )
        return {"count": _count(result)}

    def _compact_memory(self, cycle_run: CognitiveCycleRun, dry_run: bool) -> dict[str, Any]:
        max_records = int(
            cycle_run.input.get(
                "compaction_max_records",
                getattr(self._settings, "cycle_default_compaction_max_records", 100),
            )
        )
        result = _safe_call(
            self._memory_compaction_service,
            "compact",
            MemoryCompactionRequest(
                trace_id=cycle_run.trace_id,
                actor_id=cycle_run.actor_id,
                workspace_id=cycle_run.workspace_id,
                owner_scope=cycle_run.owner_scope,
                dry_run=dry_run,
                max_input_records=max_records,
                approval_present=cycle_run.input.get("approval_present") is True,
            ),
        )
        payload = _model_or_dict(result)
        return {"runs": 1 if result is not None else 0, "dry_run": dry_run, "result": payload}

    def _create_reflections(self, cycle_run: CognitiveCycleRun, dry_run: bool) -> int:
        if dry_run or not bool(cycle_run.input.get("create_reflections")):
            return 0
        result = _safe_call(self._reflection_engine, "create_cycle_reflection", cycle_run)
        return 1 if result is not None else 0

    def _create_skill_candidates(self, cycle_run: CognitiveCycleRun, dry_run: bool) -> int:
        if dry_run or not bool(cycle_run.input.get("create_skill_candidates")):
            return 0
        result = _safe_call(self._skill_service, "create_candidate_from_cycle", cycle_run)
        return _count(result)

    def _run_regression(self, cycle_run: CognitiveCycleRun) -> int:
        if not bool(cycle_run.input.get("run_regression")):
            return 0
        result = _safe_call(
            self._regression_service,
            "run_regression",
            cycle_run.input.get("regression"),
        )
        payload = _model_or_dict(result)
        fallback = payload.get("checked", 1 if result is not None else 0)
        return int(payload.get("case_count", fallback))

    def _create_visual_snapshot(self, cycle_run: CognitiveCycleRun, dry_run: bool) -> int:
        if dry_run:
            return 0
        result = _safe_call(
            self._visual_service,
            "create_snapshot_for_cycle",
            cycle_run.trace_id,
            cycle_run.owner_scope,
        )
        return 1 if result is not None else 0

    def _observability_summary(self, cycle_run: CognitiveCycleRun) -> dict[str, Any]:
        result = _safe_call(
            self._observability_service,
            "summarize",
            cycle_run.owner_scope,
        )
        return _model_or_dict(result)

    def _emit(
        self,
        event_type: str,
        node_type: str,
        node_id: str,
        intensity: float,
        payload: dict[str, Any],
        trace_id: str | None,
    ) -> None:
        if self._telemetry_service is None:
            return
        event = VisualTelemetryEvent(
            telemetry_id=f"telemetry-{node_id}-{event_type}",
            trace_id=trace_id or node_id,
            event_type=event_type,  # type: ignore[arg-type]
            node_type=node_type,  # type: ignore[arg-type]
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
                return
            save = getattr(self._telemetry_service, "save_visual_telemetry", None)
            if callable(save):
                save(event.trace_id, [event])
        except Exception:
            return


def _safe_call(target: object | None, method: str, *args: Any, **kwargs: Any) -> Any:
    if target is None:
        return None
    fn = getattr(target, method, None)
    if not callable(fn):
        return None
    return fn(*args, **kwargs)


def _model_or_dict(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    dump = getattr(value, "model_dump", None)
    if callable(dump):
        payload = dump(mode="json")
        return cast(dict[str, Any], payload) if isinstance(payload, dict) else {}
    if isinstance(value, dict):
        return value
    return {"value": str(value)}


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _count(value: Any) -> int:
    if value is None:
        return 0
    if isinstance(value, (list, tuple, set)):
        return len(value)
    if isinstance(value, dict):
        for key in ("count", "created", "checked", "total"):
            if isinstance(value.get(key), int):
                return int(value[key])
        return len(value)
    return 1
