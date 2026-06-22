"""Deterministic run status sampler."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import cast

from aion_brain.contracts.run_supervision import RunStatusSample, RunSupervisionRecord
from aion_brain.contracts.scopes import ActorContext
from aion_brain.dialogue._shared import authorize, emit_telemetry

_TERMINAL_STATUS_TO_RUN_STATUS = {
    "completed": "completed",
    "failed": "failed",
    "cancelled": "cancelled",
    "blocked": "blocked",
}


class RunStatusSampler:
    """Sample supervised target status and update the local supervision record."""

    def __init__(
        self,
        repository: object,
        target_adapter: object,
        policy_adapter: object | None,
        *,
        telemetry_service: object | None = None,
        audit_sink: object | None = None,
        provenance_service: object | None = None,
        settings: object | None = None,
        actor_context: ActorContext | None = None,
    ) -> None:
        self._repository = repository
        self._target_adapter = target_adapter
        self._policy_adapter = policy_adapter
        self._telemetry_service = telemetry_service
        self._audit_sink = audit_sink
        self._provenance_service = provenance_service
        self._settings = settings
        self._actor_context = actor_context or ActorContext()

    def with_actor_context(self, actor_context: ActorContext) -> RunStatusSampler:
        return RunStatusSampler(
            self._repository,
            self._target_adapter,
            self._policy_adapter,
            telemetry_service=self._telemetry_service,
            audit_sink=self._audit_sink,
            provenance_service=self._provenance_service,
            settings=self._settings,
            actor_context=actor_context,
        )

    def sample(self, run_supervision_id: str, scope: list[str]) -> RunStatusSample:
        authorize(
            self._policy_adapter,
            action_type="run_supervision.sample",
            resource_type="run_supervision",
            resource_id=run_supervision_id,
            scope=scope,
            risk_level="low",
        )
        run = _require_run(self._repository, run_supervision_id)
        if not _scope_matches(run.owner_scope, scope):
            raise PermissionError("scope_not_allowed")
        sample_call = getattr(self._target_adapter, "sample", None)
        if not callable(sample_call):
            raise RuntimeError("run_target_status_adapter_unavailable")
        sample = sample_call(
            run.target_system,
            run.target_run_id,
            {
                "run_supervision_id": run.run_supervision_id,
                "trace_id": run.trace_id,
                "scope": run.owner_scope,
            },
        )
        if not isinstance(sample, RunStatusSample):
            raise TypeError("target adapter returned a non-RunStatusSample value")
        save_sample = getattr(self._repository, "save_sample", None)
        stored = save_sample(sample) if callable(save_sample) else sample
        updated = self._updated_run(run, stored)
        save_run = getattr(self._repository, "save_run", None)
        if callable(save_run):
            save_run(updated)
        _record(
            self._audit_sink,
            {"event_type": "run_status_sampled", "id": stored.run_status_sample_id},
        )
        _link(
            self._provenance_service,
            run.run_supervision_id,
            stored.run_status_sample_id,
            "sampled_as",
        )
        emit_telemetry(
            self._telemetry_service,
            event_type="run_status_sampled",
            node_type="run_status_sample",
            node_id=stored.run_status_sample_id,
            intensity=0.4,
            trace_id=stored.trace_id,
            edge_from=run.run_supervision_id,
            edge_to=stored.run_status_sample_id,
            payload={"observed_status": stored.observed_status},
        )
        if updated.stalled:
            emit_telemetry(
                self._telemetry_service,
                event_type="run_stalled_detected",
                node_type="run_supervision",
                node_id=run.run_supervision_id,
                intensity=0.9,
                trace_id=run.trace_id,
                payload={"current_status": updated.current_status},
            )
        return cast(RunStatusSample, stored)

    def sample_many(
        self, scope: list[str], status: str | None = "active", limit: int = 100
    ) -> list[RunStatusSample]:
        list_runs = getattr(self._repository, "list_runs", None)
        if not callable(list_runs):
            return []
        runs = list_runs(scope=scope, status=status, limit=limit)
        return [self.sample(run.run_supervision_id, scope) for run in runs]

    def _updated_run(
        self, run: RunSupervisionRecord, sample: RunStatusSample
    ) -> RunSupervisionRecord:
        now = sample.observed_at or datetime.now(UTC)
        terminal_status = _TERMINAL_STATUS_TO_RUN_STATUS.get(sample.observed_status)
        stalled = _is_stalled(run, sample, now, self._stall_seconds())
        status = terminal_status or ("stalled" if stalled else run.status)
        return run.model_copy(
            update={
                "previous_status": run.current_status,
                "current_status": sample.observed_status,
                "status": status,
                "last_sample_id": sample.run_status_sample_id,
                "last_seen_at": now,
                "stalled": stalled,
                "completed_at": now if terminal_status is not None else run.completed_at,
                "updated_at": datetime.now(UTC),
            }
        )

    def _stall_seconds(self) -> int:
        return int(getattr(self._settings, "run_supervision_default_stall_seconds", 900))


def _is_stalled(
    run: RunSupervisionRecord, sample: RunStatusSample, now: datetime, stall_seconds: int
) -> bool:
    if sample.observed_status == "unknown" and run.status == "active":
        return True
    if sample.observed_status != "running":
        return False
    anchor = run.last_seen_at or run.created_at
    if anchor is None:
        return False
    return _aware(anchor) <= _aware(now) - timedelta(seconds=stall_seconds)


def _aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value


def _require_run(repository: object, run_supervision_id: str) -> RunSupervisionRecord:
    get = getattr(repository, "get_run", None)
    run = get(run_supervision_id) if callable(get) else None
    if not isinstance(run, RunSupervisionRecord):
        raise ValueError("run_supervision_not_found")
    return run


def _scope_matches(owner_scope: list[str], scope: list[str]) -> bool:
    return bool(set(owner_scope).intersection(scope))


def _record(audit_sink: object | None, payload: dict[str, object]) -> None:
    record = getattr(audit_sink, "record_event", None)
    if callable(record):
        try:
            record(payload)
        except Exception:
            return


def _link(
    provenance_service: object | None, source_id: str, target_id: str, relation_type: str
) -> None:
    link = getattr(provenance_service, "record_link", None)
    if callable(link):
        try:
            link(source_id, target_id, relation_type)
        except Exception:
            return


__all__ = ["RunStatusSampler"]
