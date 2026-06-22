"""Persistence for AION situation and temporal state projections."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    Float,
    Index,
    MetaData,
    Table,
    Text,
    create_engine,
    insert,
    select,
    update,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.engine import Engine, RowMapping
from sqlalchemy.pool import QueuePool, StaticPool

from aion_brain.contracts.situations import (
    ContextContinuityRecord,
    SituationProjectionResult,
    SituationQuery,
    SituationRecord,
)
from aion_brain.contracts.temporal_state import (
    StateAtom,
    StateTransition,
    TemporalStateWindow,
)

situation_metadata = MetaData()
json_payload_type = JSON().with_variant(JSONB(), "postgresql")

aion_situations = Table(
    "aion_situations",
    situation_metadata,
    Column("situation_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("actor_id", Text, nullable=True),
    Column("workspace_id", Text, nullable=True),
    Column("status", Text, nullable=False),
    Column("situation_type", Text, nullable=False),
    Column("title", Text, nullable=False),
    Column("summary", Text, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("active_goal_ids", json_payload_type, nullable=False),
    Column("active_task_ids", json_payload_type, nullable=False),
    Column("active_workflow_run_ids", json_payload_type, nullable=False),
    Column("active_focus_session_ids", json_payload_type, nullable=False),
    Column("entity_refs", json_payload_type, nullable=False),
    Column("belief_refs", json_payload_type, nullable=False),
    Column("evidence_refs", json_payload_type, nullable=False),
    Column("memory_refs", json_payload_type, nullable=False),
    Column("constraints", json_payload_type, nullable=False),
    Column("confidence", Float, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=True),
    Column("updated_at", DateTime(timezone=True), nullable=True),
    Column("closed_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_situations_trace_id", "trace_id"),
    Index("ix_aion_situations_actor_id", "actor_id"),
    Index("ix_aion_situations_workspace_id", "workspace_id"),
    Index("ix_aion_situations_status", "status"),
    Index("ix_aion_situations_situation_type", "situation_type"),
    Index("ix_aion_situations_confidence", "confidence"),
    Index("ix_aion_situations_created_at", "created_at"),
    Index("ix_aion_situations_updated_at", "updated_at"),
)

aion_state_atoms = Table(
    "aion_state_atoms",
    situation_metadata,
    Column("state_atom_id", Text, primary_key=True),
    Column("situation_id", Text, nullable=True),
    Column("trace_id", Text, nullable=True),
    Column("atom_type", Text, nullable=False),
    Column("source_type", Text, nullable=False),
    Column("source_id", Text, nullable=False),
    Column("subject_ref", Text, nullable=True),
    Column("predicate", Text, nullable=False),
    Column("object_ref", Text, nullable=True),
    Column("value", json_payload_type, nullable=False),
    Column("status", Text, nullable=False),
    Column("confidence", Float, nullable=False),
    Column("sensitivity", Text, nullable=False),
    Column("observed_at", DateTime(timezone=True), nullable=False),
    Column("valid_from", DateTime(timezone=True), nullable=True),
    Column("valid_to", DateTime(timezone=True), nullable=True),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("evidence_refs", json_payload_type, nullable=False),
    Column("belief_refs", json_payload_type, nullable=False),
    Column("entity_refs", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=True),
    Column("superseded_at", DateTime(timezone=True), nullable=True),
    Column("deleted_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_state_atoms_situation_id", "situation_id"),
    Index("ix_aion_state_atoms_trace_id", "trace_id"),
    Index("ix_aion_state_atoms_atom_type", "atom_type"),
    Index("ix_aion_state_atoms_source_type_source_id", "source_type", "source_id"),
    Index("ix_aion_state_atoms_subject_ref", "subject_ref"),
    Index("ix_aion_state_atoms_predicate", "predicate"),
    Index("ix_aion_state_atoms_object_ref", "object_ref"),
    Index("ix_aion_state_atoms_status", "status"),
    Index("ix_aion_state_atoms_confidence", "confidence"),
    Index("ix_aion_state_atoms_sensitivity", "sensitivity"),
    Index("ix_aion_state_atoms_observed_at", "observed_at"),
    Index("ix_aion_state_atoms_valid_from", "valid_from"),
    Index("ix_aion_state_atoms_valid_to", "valid_to"),
    Index("ix_aion_state_atoms_deleted_at", "deleted_at"),
    Index("ix_aion_state_atoms_created_at", "created_at"),
)

aion_temporal_state_windows = Table(
    "aion_temporal_state_windows",
    situation_metadata,
    Column("temporal_window_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("actor_id", Text, nullable=True),
    Column("workspace_id", Text, nullable=True),
    Column("window_type", Text, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("start_at", DateTime(timezone=True), nullable=False),
    Column("end_at", DateTime(timezone=True), nullable=False),
    Column("state_atom_ids", json_payload_type, nullable=False),
    Column("event_ids", json_payload_type, nullable=False),
    Column("situation_ids", json_payload_type, nullable=False),
    Column("summary", Text, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_temporal_windows_trace_id", "trace_id"),
    Index("ix_aion_temporal_windows_actor_id", "actor_id"),
    Index("ix_aion_temporal_windows_workspace_id", "workspace_id"),
    Index("ix_aion_temporal_windows_window_type", "window_type"),
    Index("ix_aion_temporal_windows_start_at", "start_at"),
    Index("ix_aion_temporal_windows_end_at", "end_at"),
    Index("ix_aion_temporal_windows_created_at", "created_at"),
)

aion_situation_projection_runs = Table(
    "aion_situation_projection_runs",
    situation_metadata,
    Column("projection_run_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("actor_id", Text, nullable=True),
    Column("workspace_id", Text, nullable=True),
    Column("status", Text, nullable=False),
    Column("mode", Text, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("input", json_payload_type, nullable=False),
    Column("situation_ids", json_payload_type, nullable=False),
    Column("state_atom_ids", json_payload_type, nullable=False),
    Column("transition_ids", json_payload_type, nullable=False),
    Column("warnings", json_payload_type, nullable=False),
    Column("result", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=True),
    Column("completed_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_projection_runs_trace_id", "trace_id"),
    Index("ix_aion_projection_runs_actor_id", "actor_id"),
    Index("ix_aion_projection_runs_workspace_id", "workspace_id"),
    Index("ix_aion_projection_runs_status", "status"),
    Index("ix_aion_projection_runs_mode", "mode"),
    Index("ix_aion_projection_runs_created_at", "created_at"),
)

aion_state_transitions = Table(
    "aion_state_transitions",
    situation_metadata,
    Column("state_transition_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("situation_id", Text, nullable=True),
    Column("transition_type", Text, nullable=False),
    Column("from_state_atom_id", Text, nullable=True),
    Column("to_state_atom_id", Text, nullable=True),
    Column("source_type", Text, nullable=False),
    Column("source_id", Text, nullable=True),
    Column("status", Text, nullable=False),
    Column("confidence", Float, nullable=False),
    Column("reason", Text, nullable=False),
    Column("evidence_refs", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_state_transitions_trace_id", "trace_id"),
    Index("ix_aion_state_transitions_situation_id", "situation_id"),
    Index("ix_aion_state_transitions_transition_type", "transition_type"),
    Index("ix_aion_state_transitions_from_atom", "from_state_atom_id"),
    Index("ix_aion_state_transitions_to_atom", "to_state_atom_id"),
    Index("ix_aion_state_transitions_source_type_source_id", "source_type", "source_id"),
    Index("ix_aion_state_transitions_status", "status"),
    Index("ix_aion_state_transitions_confidence", "confidence"),
    Index("ix_aion_state_transitions_created_at", "created_at"),
)

aion_context_continuity_records = Table(
    "aion_context_continuity_records",
    situation_metadata,
    Column("continuity_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("actor_id", Text, nullable=True),
    Column("workspace_id", Text, nullable=True),
    Column("dialogue_session_id", Text, nullable=True),
    Column("focus_session_id", Text, nullable=True),
    Column("situation_id", Text, nullable=True),
    Column("continuity_type", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("carried_refs", json_payload_type, nullable=False),
    Column("dropped_refs", json_payload_type, nullable=False),
    Column("constraints", json_payload_type, nullable=False),
    Column("reason", Text, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_continuity_trace_id", "trace_id"),
    Index("ix_aion_continuity_actor_id", "actor_id"),
    Index("ix_aion_continuity_workspace_id", "workspace_id"),
    Index("ix_aion_continuity_dialogue_session_id", "dialogue_session_id"),
    Index("ix_aion_continuity_focus_session_id", "focus_session_id"),
    Index("ix_aion_continuity_situation_id", "situation_id"),
    Index("ix_aion_continuity_type", "continuity_type"),
    Index("ix_aion_continuity_status", "status"),
    Index("ix_aion_continuity_created_at", "created_at"),
)


class SituationRepository:
    """Repository for situation projections, state atoms, and continuity records."""

    def __init__(
        self,
        database_url: str | None = None,
        *,
        engine: Engine | None = None,
        auto_create: bool = True,
    ) -> None:
        url = database_url or "sqlite+pysqlite:///:memory:"
        self._engine = engine or create_engine(
            url,
            connect_args={"check_same_thread": False} if url.startswith("sqlite") else {},
            poolclass=StaticPool if url.startswith("sqlite") else QueuePool,
            pool_pre_ping=not url.startswith("sqlite"),
        )
        self._auto_create = auto_create
        self._schema_ready = False

    def save_situation(self, situation: SituationRecord) -> SituationRecord:
        self._upsert(aion_situations, "situation_id", situation.model_dump(mode="python"))
        return situation

    def get_situation(self, situation_id: str) -> SituationRecord | None:
        row = self._first(
            select(aion_situations).where(aion_situations.c.situation_id == situation_id)
        )
        return SituationRecord(**dict(row)) if row is not None else None

    def query_situations(self, query: SituationQuery) -> list[SituationRecord]:
        statement = select(aion_situations).order_by(aion_situations.c.updated_at.desc())
        if query.trace_id:
            statement = statement.where(aion_situations.c.trace_id == query.trace_id)
        if query.actor_id:
            statement = statement.where(aion_situations.c.actor_id == query.actor_id)
        if query.workspace_id:
            statement = statement.where(aion_situations.c.workspace_id == query.workspace_id)
        if query.statuses:
            statement = statement.where(aion_situations.c.status.in_(query.statuses))
        if query.situation_types:
            statement = statement.where(aion_situations.c.situation_type.in_(query.situation_types))
        rows = self._all(statement)
        needle = query.text.lower() if query.text else None
        refs = set(query.refs)
        results: list[SituationRecord] = []
        for row in rows:
            situation = SituationRecord(**dict(row))
            if not _scope_matches(situation.owner_scope, query.scope):
                continue
            if (
                needle
                and needle not in situation.title.lower()
                and needle not in situation.summary.lower()
            ):
                continue
            if refs and not refs.intersection(_situation_refs(situation)):
                continue
            results.append(situation)
            if len(results) >= query.limit:
                break
        return results

    def save_state_atom(self, atom: StateAtom) -> StateAtom:
        self._upsert(aion_state_atoms, "state_atom_id", atom.model_dump(mode="python"))
        return atom

    def get_state_atom(self, state_atom_id: str) -> StateAtom | None:
        row = self._first(
            select(aion_state_atoms).where(aion_state_atoms.c.state_atom_id == state_atom_id)
        )
        return StateAtom(**dict(row)) if row is not None else None

    def list_state_atoms(
        self,
        *,
        scope: list[str],
        situation_id: str | None = None,
        trace_id: str | None = None,
        statuses: list[str] | None = None,
        source_type: str | None = None,
        source_id: str | None = None,
        include_deleted: bool = False,
        limit: int = 100,
    ) -> list[StateAtom]:
        statement = select(aion_state_atoms).order_by(aion_state_atoms.c.created_at.desc())
        if situation_id:
            statement = statement.where(aion_state_atoms.c.situation_id == situation_id)
        if trace_id:
            statement = statement.where(aion_state_atoms.c.trace_id == trace_id)
        if statuses:
            statement = statement.where(aion_state_atoms.c.status.in_(statuses))
        if source_type:
            statement = statement.where(aion_state_atoms.c.source_type == source_type)
        if source_id:
            statement = statement.where(aion_state_atoms.c.source_id == source_id)
        if not include_deleted:
            statement = statement.where(aion_state_atoms.c.deleted_at.is_(None))
        atoms: list[StateAtom] = []
        for row in self._all(statement):
            atom = StateAtom(**dict(row))
            if not _scope_matches(atom.owner_scope, scope):
                continue
            atoms.append(atom)
            if len(atoms) >= limit:
                break
        return atoms

    def save_transition(self, transition: StateTransition) -> StateTransition:
        self._upsert(
            aion_state_transitions,
            "state_transition_id",
            transition.model_dump(mode="python"),
        )
        return transition

    def list_transitions(
        self,
        *,
        trace_id: str | None = None,
        situation_id: str | None = None,
        status: str | None = None,
        limit: int = 100,
    ) -> list[StateTransition]:
        statement = select(aion_state_transitions).order_by(
            aion_state_transitions.c.created_at.desc()
        )
        if trace_id:
            statement = statement.where(aion_state_transitions.c.trace_id == trace_id)
        if situation_id:
            statement = statement.where(aion_state_transitions.c.situation_id == situation_id)
        if status:
            statement = statement.where(aion_state_transitions.c.status == status)
        return [StateTransition(**dict(row)) for row in self._all(statement)[:limit]]

    def save_temporal_window(self, window: TemporalStateWindow) -> TemporalStateWindow:
        self._upsert(
            aion_temporal_state_windows,
            "temporal_window_id",
            window.model_dump(mode="python"),
        )
        return window

    def get_temporal_window(self, temporal_window_id: str) -> TemporalStateWindow | None:
        row = self._first(
            select(aion_temporal_state_windows).where(
                aion_temporal_state_windows.c.temporal_window_id == temporal_window_id
            )
        )
        return TemporalStateWindow(**dict(row)) if row is not None else None

    def list_temporal_windows(
        self,
        *,
        scope: list[str],
        trace_id: str | None = None,
        window_type: str | None = None,
        limit: int = 100,
    ) -> list[TemporalStateWindow]:
        statement = select(aion_temporal_state_windows).order_by(
            aion_temporal_state_windows.c.created_at.desc()
        )
        if trace_id:
            statement = statement.where(aion_temporal_state_windows.c.trace_id == trace_id)
        if window_type:
            statement = statement.where(aion_temporal_state_windows.c.window_type == window_type)
        windows: list[TemporalStateWindow] = []
        for row in self._all(statement):
            window = TemporalStateWindow(**dict(row))
            if not _scope_matches(window.owner_scope, scope):
                continue
            windows.append(window)
            if len(windows) >= limit:
                break
        return windows

    def save_projection_run(self, run: SituationProjectionResult) -> SituationProjectionResult:
        values = run.model_dump(mode="python")
        payload = {
            key: values[key]
            for key in (
                "projection_run_id",
                "trace_id",
                "actor_id",
                "workspace_id",
                "status",
                "mode",
                "owner_scope",
                "input",
                "situation_ids",
                "state_atom_ids",
                "transition_ids",
                "warnings",
                "result",
                "created_by",
                "created_at",
                "completed_at",
            )
        }
        payload["result"] = {
            **payload["result"],
            "situations": [item.model_dump(mode="json") for item in run.situations],
            "state_atoms": [item.model_dump(mode="json") for item in run.state_atoms],
            "transitions": [item.model_dump(mode="json") for item in run.transitions],
        }
        self._upsert(aion_situation_projection_runs, "projection_run_id", payload)
        return run

    def get_projection_run(self, projection_run_id: str) -> SituationProjectionResult | None:
        row = self._first(
            select(aion_situation_projection_runs).where(
                aion_situation_projection_runs.c.projection_run_id == projection_run_id
            )
        )
        if row is None:
            return None
        data = dict(row)
        result = dict(data.get("result") or {})
        data["situations"] = result.pop("situations", [])
        data["state_atoms"] = result.pop("state_atoms", [])
        data["transitions"] = result.pop("transitions", [])
        data["result"] = result
        return SituationProjectionResult(**data)

    def list_projection_runs(
        self,
        *,
        status: str | None = None,
        limit: int = 100,
    ) -> list[SituationProjectionResult]:
        statement = select(aion_situation_projection_runs).order_by(
            aion_situation_projection_runs.c.created_at.desc()
        )
        if status:
            statement = statement.where(aion_situation_projection_runs.c.status == status)
        runs: list[SituationProjectionResult] = []
        for row in self._all(statement):
            run = self.get_projection_run(str(row["projection_run_id"]))
            if run is not None:
                runs.append(run)
            if len(runs) >= limit:
                break
        return runs

    def save_continuity(self, record: ContextContinuityRecord) -> ContextContinuityRecord:
        self._upsert(
            aion_context_continuity_records,
            "continuity_id",
            record.model_dump(mode="python"),
        )
        return record

    def list_continuity(
        self,
        *,
        scope: list[str],
        trace_id: str | None = None,
        dialogue_session_id: str | None = None,
        focus_session_id: str | None = None,
        situation_id: str | None = None,
        limit: int = 100,
    ) -> list[ContextContinuityRecord]:
        statement = select(aion_context_continuity_records).order_by(
            aion_context_continuity_records.c.created_at.desc()
        )
        if trace_id:
            statement = statement.where(aion_context_continuity_records.c.trace_id == trace_id)
        if dialogue_session_id:
            statement = statement.where(
                aion_context_continuity_records.c.dialogue_session_id == dialogue_session_id
            )
        if focus_session_id:
            statement = statement.where(
                aion_context_continuity_records.c.focus_session_id == focus_session_id
            )
        if situation_id:
            statement = statement.where(
                aion_context_continuity_records.c.situation_id == situation_id
            )
        records: list[ContextContinuityRecord] = []
        for row in self._all(statement):
            record = ContextContinuityRecord(**dict(row))
            owner_scope = _continuity_scope(record)
            if owner_scope and not _scope_matches(owner_scope, scope):
                continue
            records.append(record)
            if len(records) >= limit:
                break
        return records

    def status(self, scope: list[str] | None = None) -> dict[str, object]:
        query = SituationQuery(scope=scope or ["workspace:main"], statuses=["active"], limit=1000)
        return {
            "status": "healthy",
            "active_situation_count": len(self.query_situations(query)),
        }

    def _upsert(self, table: Table, key: str, values: dict[str, Any]) -> None:
        self._ensure_schema()
        with self._engine.begin() as connection:
            existing = connection.execute(
                select(table.c[key]).where(table.c[key] == values[key])
            ).first()
            if existing is None:
                connection.execute(insert(table).values(**values))
            else:
                connection.execute(
                    update(table).where(table.c[key] == values[key]).values(**values)
                )

    def _ensure_schema(self) -> None:
        if self._schema_ready:
            return
        if self._auto_create:
            situation_metadata.create_all(self._engine)
        self._schema_ready = True

    def _first(self, statement: Any) -> RowMapping | None:
        self._ensure_schema()
        with self._engine.begin() as connection:
            return connection.execute(statement).mappings().first()

    def _all(self, statement: Any) -> list[RowMapping]:
        self._ensure_schema()
        with self._engine.begin() as connection:
            return list(connection.execute(statement).mappings().all())


def _scope_matches(owner_scope: list[str], requested_scope: list[str]) -> bool:
    return bool(set(owner_scope).intersection(set(requested_scope)))


def _situation_refs(situation: SituationRecord) -> set[str]:
    refs: set[str] = set()
    for items in (
        situation.active_goal_ids,
        situation.active_task_ids,
        situation.active_workflow_run_ids,
        situation.active_focus_session_ids,
        situation.entity_refs,
        situation.belief_refs,
        situation.evidence_refs,
        situation.memory_refs,
    ):
        refs.update(items)
    return refs


def _continuity_scope(record: ContextContinuityRecord) -> list[str]:
    raw = record.metadata.get("owner_scope")
    if isinstance(raw, list):
        return [str(item) for item in raw]
    return []


def now_utc() -> datetime:
    """Return current UTC time for situation services."""
    return datetime.now(UTC)


__all__ = [
    "SituationRepository",
    "aion_context_continuity_records",
    "aion_situation_projection_runs",
    "aion_situations",
    "aion_state_atoms",
    "aion_state_transitions",
    "aion_temporal_state_windows",
    "now_utc",
    "situation_metadata",
]
