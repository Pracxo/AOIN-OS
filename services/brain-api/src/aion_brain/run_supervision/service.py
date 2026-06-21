"""Run supervision service."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from aion_brain.contracts.run_supervision import RunSupervisionCreateRequest, RunSupervisionRecord
from aion_brain.contracts.scopes import ActorContext
from aion_brain.dialogue._shared import authorize, emit_telemetry


class RunSupervisionService:
    """Create and manage canonical supervision records."""

    def __init__(
        self,
        repository: object,
        policy_adapter: object | None,
        *,
        telemetry_service: object | None = None,
        audit_sink: object | None = None,
        provenance_service: object | None = None,
        settings: object | None = None,
        actor_context: ActorContext | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._telemetry_service = telemetry_service
        self._audit_sink = audit_sink
        self._provenance_service = provenance_service
        self._settings = settings
        self._actor_context = actor_context or ActorContext()

    def with_actor_context(self, actor_context: ActorContext) -> RunSupervisionService:
        return RunSupervisionService(
            self._repository,
            self._policy_adapter,
            telemetry_service=self._telemetry_service,
            audit_sink=self._audit_sink,
            provenance_service=self._provenance_service,
            settings=self._settings,
            actor_context=actor_context,
        )

    def create(self, request: RunSupervisionCreateRequest) -> RunSupervisionRecord:
        if self._settings is not None and not bool(
            getattr(self._settings, "run_supervision_enabled", True)
        ):
            raise RuntimeError("run_supervision_disabled")
        authorize(
            self._policy_adapter,
            action_type="run_supervision.create",
            resource_type="run_supervision",
            resource_id=request.run_supervision_id,
            scope=request.owner_scope,
            trace_id=request.trace_id or self._actor_context.trace_id,
            actor_id=request.actor_id or self._actor_context.actor_id,
            workspace_id=request.workspace_id or self._actor_context.workspace_id,
            risk_level="medium",
        )
        now = datetime.now(UTC)
        run = RunSupervisionRecord(
            run_supervision_id=request.run_supervision_id or f"run-supervision-{uuid4().hex}",
            trace_id=request.trace_id or self._actor_context.trace_id,
            actor_id=request.actor_id or self._actor_context.actor_id,
            workspace_id=request.workspace_id or self._actor_context.workspace_id,
            source_type=request.source_type,
            source_id=request.source_id,
            target_system=request.target_system,
            target_run_id=request.target_run_id,
            status="active",
            run_type=request.run_type,
            owner_scope=request.owner_scope,
            title=request.title,
            description=request.description,
            current_status="unknown",
            previous_status=None,
            timeout_policy_id=request.timeout_policy_id,
            deadline_at=request.deadline_at,
            last_sample_id=None,
            last_seen_at=None,
            stalled=False,
            cancellable=request.cancellable,
            pausable=request.pausable,
            resumable=request.resumable,
            compensation_available=request.compensation_available,
            outcome_id=None,
            metadata={**request.metadata, "supervision_observes_only": True},
            created_by=request.created_by or self._actor_context.actor_id,
            created_at=now,
            updated_at=now,
        )
        stored = _save_run(self._repository, run)
        _record(
            self._audit_sink,
            {"event_type": "run_supervision_created", "id": stored.run_supervision_id},
        )
        _link(
            self._provenance_service,
            stored.source_id,
            stored.run_supervision_id,
            "supervised_as",
        )
        emit_telemetry(
            self._telemetry_service,
            event_type="run_supervision_created",
            node_type="run_supervision",
            node_id=stored.run_supervision_id,
            intensity=0.5,
            trace_id=stored.trace_id,
            payload={"target_system": stored.target_system, "status": stored.status},
        )
        return stored

    def get(self, run_supervision_id: str, scope: list[str]) -> RunSupervisionRecord | None:
        authorize(
            self._policy_adapter,
            action_type="run_supervision.read",
            resource_type="run_supervision",
            resource_id=run_supervision_id,
            scope=scope,
            risk_level="low",
        )
        run = _get_run(self._repository, run_supervision_id)
        if run is None or not _scope_matches(run.owner_scope, scope) or run.deleted_at is not None:
            return None
        return run

    def query(
        self,
        scope: list[str],
        target_system: str | None = None,
        status: str | None = None,
        stalled: bool | None = None,
        limit: int = 100,
    ) -> list[RunSupervisionRecord]:
        authorize(
            self._policy_adapter,
            action_type="run_supervision.read",
            resource_type="run_supervision",
            resource_id=None,
            scope=scope,
            risk_level="low",
        )
        list_runs = getattr(self._repository, "list_runs", None)
        if not callable(list_runs):
            return []
        result = list_runs(
            scope=scope,
            target_system=target_system,
            status=status,
            stalled=stalled,
            limit=limit,
        )
        return [item for item in result if isinstance(item, RunSupervisionRecord)]

    def archive(
        self, run_supervision_id: str, actor_id: str | None, reason: str
    ) -> RunSupervisionRecord:
        run = _require_run(self._repository, run_supervision_id)
        authorize(
            self._policy_adapter,
            action_type="run_supervision.update",
            resource_type="run_supervision",
            resource_id=run_supervision_id,
            scope=run.owner_scope,
            actor_id=actor_id or self._actor_context.actor_id,
            risk_level="medium",
            context={"reason": reason},
        )
        archived = run.model_copy(
            update={
                "status": "archived",
                "archived_at": datetime.now(UTC),
                "updated_at": datetime.now(UTC),
                "metadata": {**run.metadata, "archive_reason": reason},
            }
        )
        return _save_run(self._repository, archived)

    def soft_delete(self, run_supervision_id: str, actor_id: str | None, reason: str) -> bool:
        run = _require_run(self._repository, run_supervision_id)
        authorize(
            self._policy_adapter,
            action_type="run_supervision.delete",
            resource_type="run_supervision",
            resource_id=run_supervision_id,
            scope=run.owner_scope,
            actor_id=actor_id or self._actor_context.actor_id,
            risk_level="medium",
            context={"reason": reason},
        )
        _save_run(
            self._repository,
            run.model_copy(
                update={
                    "status": "archived",
                    "deleted_at": datetime.now(UTC),
                    "updated_at": datetime.now(UTC),
                    "metadata": {**run.metadata, "delete_reason": reason},
                }
            ),
        )
        return True


def _save_run(repository: object, run: RunSupervisionRecord) -> RunSupervisionRecord:
    save = getattr(repository, "save_run", None)
    stored = save(run) if callable(save) else run
    return stored if isinstance(stored, RunSupervisionRecord) else run


def _get_run(repository: object, run_supervision_id: str) -> RunSupervisionRecord | None:
    get = getattr(repository, "get_run", None)
    run = get(run_supervision_id) if callable(get) else None
    return run if isinstance(run, RunSupervisionRecord) else None


def _require_run(repository: object, run_supervision_id: str) -> RunSupervisionRecord:
    run = _get_run(repository, run_supervision_id)
    if run is None:
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


__all__ = ["RunSupervisionService"]
