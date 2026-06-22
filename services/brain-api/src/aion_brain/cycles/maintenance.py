"""Safe deterministic cognitive maintenance steps."""

from typing import Any, cast

from aion_brain.contracts.cycles import CognitiveCycleRun, CognitiveCycleStep
from aion_brain.contracts.memory_governance import (
    MemoryCompactionRequest,
    MemoryConflictScanRequest,
)


class MaintenanceService:
    """Dispatch generic cycle steps to existing Brain service boundaries."""

    def __init__(
        self,
        *,
        attention_controller: object | None = None,
        focus_service: object | None = None,
        working_memory_service: object | None = None,
        memory_decay_service: object | None = None,
        memory_conflict_service: object | None = None,
        memory_compaction_service: object | None = None,
        reflection_engine: object | None = None,
        regression_service: object | None = None,
        replay_service: object | None = None,
        visual_service: object | None = None,
        observability_service: object | None = None,
        approval_service: object | None = None,
        workflow_worker: object | None = None,
        kernel_self_test_service: object | None = None,
        settings: object | None = None,
    ) -> None:
        self._attention_controller = attention_controller
        self._focus_service = focus_service
        self._working_memory_service = working_memory_service
        self._memory_decay_service = memory_decay_service
        self._memory_conflict_service = memory_conflict_service
        self._memory_compaction_service = memory_compaction_service
        self._reflection_engine = reflection_engine
        self._regression_service = regression_service
        self._replay_service = replay_service
        self._visual_service = visual_service
        self._observability_service = observability_service
        self._approval_service = approval_service
        self._workflow_worker = workflow_worker
        self._kernel_self_test_service = kernel_self_test_service
        self._settings = settings

    def run_step(
        self,
        step: CognitiveCycleStep,
        cycle_run: CognitiveCycleRun,
        dry_run: bool,
    ) -> dict[str, Any]:
        """Run or preview one safe maintenance step."""
        handlers = {
            "attention_review": self._attention_review,
            "working_memory_sweep": self._working_memory_sweep,
            "memory_decay": self._memory_decay,
            "memory_conflict_scan": self._memory_conflict_scan,
            "memory_compaction": self._memory_compaction,
            "reflection_create": self._reflection_create,
            "skill_candidate_create": self._skill_candidate_create,
            "regression_check": self._regression_check,
            "replay_check": self._replay_check,
            "visual_snapshot": self._visual_snapshot,
            "observability_summary": self._observability_summary,
            "approval_expiry": self._approval_expiry,
            "workflow_heartbeat_review": self._workflow_heartbeat_review,
            "kernel_self_test": self._kernel_self_test,
            "noop": self._noop,
        }
        return handlers[step.step_type](step, cycle_run, dry_run)

    def _attention_review(
        self,
        step: CognitiveCycleStep,
        cycle_run: CognitiveCycleRun,
        dry_run: bool,
    ) -> dict[str, Any]:
        active_focus = _safe_call(
            self._focus_service,
            "get_active_focus",
            cycle_run.actor_id,
            cycle_run.workspace_id,
            cycle_run.owner_scope,
        )
        signals = _safe_call(
            self._attention_controller,
            "list_signals",
            cycle_run.owner_scope,
            handled=False,
            limit=50,
        )
        return {
            "active_focus_present": active_focus is not None,
            "pending_attention_signals": _count(signals),
            "dry_run": dry_run,
        }

    def _working_memory_sweep(
        self,
        step: CognitiveCycleStep,
        cycle_run: CognitiveCycleRun,
        dry_run: bool,
    ) -> dict[str, Any]:
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
            return {"dry_run": True, "would_sweep": int(count or 0), "limit": limit}
        result = _safe_call(
            self._working_memory_service,
            "sweep_expired",
            cycle_run.owner_scope,
            limit,
        )
        return {
            "dry_run": False,
            "swept": int(_dict(result).get("swept", 0)),
            "result": _dict(result),
        }

    def _memory_decay(
        self,
        step: CognitiveCycleStep,
        cycle_run: CognitiveCycleRun,
        dry_run: bool,
    ) -> dict[str, Any]:
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
        return {"dry_run": dry_run, **_model_or_dict(result)}

    def _memory_conflict_scan(
        self,
        step: CognitiveCycleStep,
        cycle_run: CognitiveCycleRun,
        dry_run: bool,
    ) -> dict[str, Any]:
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
        return {"dry_run": dry_run, "conflicts_detected": _count(result)}

    def _memory_compaction(
        self,
        step: CognitiveCycleStep,
        cycle_run: CognitiveCycleRun,
        dry_run: bool,
    ) -> dict[str, Any]:
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
                strategy="deterministic_extract",
                dry_run=dry_run,
                max_input_records=max_records,
                approval_present=cycle_run.input.get("approval_present") is True,
            ),
        )
        return {"dry_run": dry_run, **_model_or_dict(result)}

    def _reflection_create(
        self,
        step: CognitiveCycleStep,
        cycle_run: CognitiveCycleRun,
        dry_run: bool,
    ) -> dict[str, Any]:
        if dry_run or not bool(cycle_run.input.get("create_reflections")):
            return {
                "skipped": True,
                "reason": "reflection_creation_not_requested",
                "dry_run": dry_run,
            }
        result = _safe_call(self._reflection_engine, "create_cycle_reflection", cycle_run)
        return {"created": 1 if result is not None else 0}

    def _skill_candidate_create(
        self,
        step: CognitiveCycleStep,
        cycle_run: CognitiveCycleRun,
        dry_run: bool,
    ) -> dict[str, Any]:
        return {
            "skipped": not bool(cycle_run.input.get("create_skill_candidates")),
            "reason": "skill_candidate_creation_requires_explicit_input",
            "dry_run": dry_run,
        }

    def _regression_check(
        self,
        step: CognitiveCycleStep,
        cycle_run: CognitiveCycleRun,
        dry_run: bool,
    ) -> dict[str, Any]:
        if not bool(cycle_run.input.get("run_regression")):
            return {"skipped": True, "reason": "regression_not_requested", "dry_run": dry_run}
        result = _safe_call(
            self._regression_service,
            "run_regression",
            cycle_run.input.get("regression"),
        )
        return {"dry_run": dry_run, **_model_or_dict(result)}

    def _replay_check(
        self,
        step: CognitiveCycleStep,
        cycle_run: CognitiveCycleRun,
        dry_run: bool,
    ) -> dict[str, Any]:
        if not bool(cycle_run.input.get("run_replay")):
            return {"skipped": True, "reason": "replay_not_requested", "dry_run": dry_run}
        result = _safe_call(self._replay_service, "run_replay", cycle_run.input.get("replay"))
        return {"dry_run": dry_run, **_model_or_dict(result)}

    def _visual_snapshot(
        self,
        step: CognitiveCycleStep,
        cycle_run: CognitiveCycleRun,
        dry_run: bool,
    ) -> dict[str, Any]:
        if dry_run:
            return {"dry_run": True, "snapshot_created": False, "metadata_only": True}
        result = _safe_call(
            self._visual_service,
            "create_snapshot_for_cycle",
            cycle_run.trace_id,
            cycle_run.owner_scope,
        )
        return {"dry_run": False, "snapshot_created": result is not None}

    def _observability_summary(
        self,
        step: CognitiveCycleStep,
        cycle_run: CognitiveCycleRun,
        dry_run: bool,
    ) -> dict[str, Any]:
        result = _safe_call(self._observability_service, "summarize", cycle_run.owner_scope)
        return {"dry_run": dry_run, "summary": _model_or_dict(result)}

    def _approval_expiry(
        self,
        step: CognitiveCycleStep,
        cycle_run: CognitiveCycleRun,
        dry_run: bool,
    ) -> dict[str, Any]:
        if dry_run:
            count = _safe_call(self._approval_service, "count_expirable", cycle_run.owner_scope)
            return {"dry_run": True, "would_expire": int(count or 0)}
        result = _safe_call(self._approval_service, "expire_pending", cycle_run.owner_scope)
        return {"dry_run": False, "expired": _count(result)}

    def _workflow_heartbeat_review(
        self,
        step: CognitiveCycleStep,
        cycle_run: CognitiveCycleRun,
        dry_run: bool,
    ) -> dict[str, Any]:
        result = _safe_call(self._workflow_worker, "summarize_heartbeats", cycle_run.owner_scope)
        return {"dry_run": dry_run, "stale_workers": int(_dict(result).get("stale_workers", 0))}

    def _kernel_self_test(
        self,
        step: CognitiveCycleStep,
        cycle_run: CognitiveCycleRun,
        dry_run: bool,
    ) -> dict[str, Any]:
        result = _safe_call(self._kernel_self_test_service, "run", dry_run=True)
        return {"dry_run": True, "result": _model_or_dict(result)}

    def _noop(
        self,
        step: CognitiveCycleStep,
        cycle_run: CognitiveCycleRun,
        dry_run: bool,
    ) -> dict[str, Any]:
        return {"noop": True, "dry_run": dry_run}


def _safe_call(target: object | None, method: str, *args: Any, **kwargs: Any) -> Any:
    if target is None:
        return None
    fn = getattr(target, method, None)
    if not callable(fn):
        return None
    return fn(*args, **kwargs)


def _count(value: Any) -> int:
    if value is None:
        return 0
    if isinstance(value, dict):
        for key in ("count", "total", "swept", "created", "expired"):
            if isinstance(value.get(key), int):
                return int(value[key])
        return len(value)
    try:
        return len(value)
    except TypeError:
        return 1


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


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
