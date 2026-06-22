"""Persistent repository for incident correlation records."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    Float,
    Index,
    Integer,
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

from aion_brain.contracts.incidents import (
    IncidentCorrelationRule,
    IncidentCorrelationRun,
    IncidentQuery,
    IncidentRecord,
    IncidentSignal,
)
from aion_brain.contracts.root_cause import RecoveryReview, RootCauseCandidate

incident_metadata = MetaData()
json_payload_type = JSON().with_variant(JSONB(), "postgresql")

aion_incident_records = Table(
    "aion_incident_records",
    incident_metadata,
    Column("incident_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("actor_id", Text, nullable=True),
    Column("workspace_id", Text, nullable=True),
    Column("status", Text, nullable=False),
    Column("incident_type", Text, nullable=False),
    Column("severity", Text, nullable=False),
    Column("title", Text, nullable=False),
    Column("summary", Text, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("primary_signal_type", Text, nullable=True),
    Column("primary_signal_id", Text, nullable=True),
    Column("signal_refs", json_payload_type, nullable=False),
    Column("alert_refs", json_payload_type, nullable=False),
    Column("notification_refs", json_payload_type, nullable=False),
    Column("run_refs", json_payload_type, nullable=False),
    Column("action_refs", json_payload_type, nullable=False),
    Column("model_output_refs", json_payload_type, nullable=False),
    Column("prompt_refs", json_payload_type, nullable=False),
    Column("grounding_refs", json_payload_type, nullable=False),
    Column("security_refs", json_payload_type, nullable=False),
    Column("audit_refs", json_payload_type, nullable=False),
    Column("scheduler_refs", json_payload_type, nullable=False),
    Column("outcome_refs", json_payload_type, nullable=False),
    Column("learning_refs", json_payload_type, nullable=False),
    Column("blocker_refs", json_payload_type, nullable=False),
    Column("root_cause_candidate_refs", json_payload_type, nullable=False),
    Column("recovery_review_refs", json_payload_type, nullable=False),
    Column("related_incident_ids", json_payload_type, nullable=False),
    Column("correlation_key", Text, nullable=False),
    Column("fingerprint", Text, nullable=False),
    Column("confidence", Float, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    Column("acknowledged_at", DateTime(timezone=True), nullable=True),
    Column("resolved_at", DateTime(timezone=True), nullable=True),
    Column("archived_at", DateTime(timezone=True), nullable=True),
    Column("deleted_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_incident_records_trace_id", "trace_id"),
    Index("ix_aion_incident_records_workspace_id", "workspace_id"),
    Index("ix_aion_incident_records_status", "status"),
    Index("ix_aion_incident_records_incident_type", "incident_type"),
    Index("ix_aion_incident_records_severity", "severity"),
    Index("ix_aion_incident_records_correlation_key", "correlation_key"),
    Index("ix_aion_incident_records_fingerprint", "fingerprint"),
    Index("ix_aion_incident_records_created_at", "created_at"),
    Index("ix_aion_incident_records_updated_at", "updated_at"),
)

aion_incident_signals = Table(
    "aion_incident_signals",
    incident_metadata,
    Column("incident_signal_id", Text, primary_key=True),
    Column("incident_id", Text, nullable=True),
    Column("trace_id", Text, nullable=True),
    Column("actor_id", Text, nullable=True),
    Column("workspace_id", Text, nullable=True),
    Column("source_type", Text, nullable=False),
    Column("source_id", Text, nullable=False),
    Column("signal_type", Text, nullable=False),
    Column("severity", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("title", Text, nullable=False),
    Column("summary", Text, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("correlation_key", Text, nullable=False),
    Column("fingerprint", Text, nullable=False),
    Column("refs", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("occurred_at", DateTime(timezone=True), nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("linked_at", DateTime(timezone=True), nullable=True),
    Column("dismissed_at", DateTime(timezone=True), nullable=True),
    Column("deleted_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_incident_signals_incident_id", "incident_id"),
    Index("ix_aion_incident_signals_trace_id", "trace_id"),
    Index("ix_aion_incident_signals_workspace_id", "workspace_id"),
    Index("ix_aion_incident_signals_source_type", "source_type"),
    Index("ix_aion_incident_signals_source_id", "source_id"),
    Index("ix_aion_incident_signals_signal_type", "signal_type"),
    Index("ix_aion_incident_signals_severity", "severity"),
    Index("ix_aion_incident_signals_status", "status"),
    Index("ix_aion_incident_signals_correlation_key", "correlation_key"),
    Index("ix_aion_incident_signals_fingerprint", "fingerprint"),
    Index("ix_aion_incident_signals_occurred_at", "occurred_at"),
    Index("ix_aion_incident_signals_created_at", "created_at"),
)

aion_incident_correlation_rules = Table(
    "aion_incident_correlation_rules",
    incident_metadata,
    Column("correlation_rule_id", Text, primary_key=True),
    Column("name", Text, nullable=False, unique=True),
    Column("description", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("rule_type", Text, nullable=False),
    Column("severity_threshold", Text, nullable=False),
    Column("source_types", json_payload_type, nullable=False),
    Column("signal_types", json_payload_type, nullable=False),
    Column("window_seconds", Integer, nullable=False),
    Column("grouping_fields", json_payload_type, nullable=False),
    Column("conditions", json_payload_type, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    Column("disabled_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_incident_rules_name", "name"),
    Index("ix_aion_incident_rules_status", "status"),
    Index("ix_aion_incident_rules_rule_type", "rule_type"),
    Index("ix_aion_incident_rules_severity_threshold", "severity_threshold"),
    Index("ix_aion_incident_rules_window_seconds", "window_seconds"),
    Index("ix_aion_incident_rules_created_at", "created_at"),
)

aion_incident_correlation_runs = Table(
    "aion_incident_correlation_runs",
    incident_metadata,
    Column("correlation_run_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("actor_id", Text, nullable=True),
    Column("workspace_id", Text, nullable=True),
    Column("status", Text, nullable=False),
    Column("mode", Text, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("window_start", DateTime(timezone=True), nullable=True),
    Column("window_end", DateTime(timezone=True), nullable=True),
    Column("rules_applied", json_payload_type, nullable=False),
    Column("signals_seen", Integer, nullable=False),
    Column("signals_linked", Integer, nullable=False),
    Column("incidents_created", Integer, nullable=False),
    Column("incidents_updated", Integer, nullable=False),
    Column("incidents_unchanged", Integer, nullable=False),
    Column("incidents", json_payload_type, nullable=False),
    Column("warnings", json_payload_type, nullable=False),
    Column("failures", json_payload_type, nullable=False),
    Column("result", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("completed_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_incident_runs_trace_id", "trace_id"),
    Index("ix_aion_incident_runs_workspace_id", "workspace_id"),
    Index("ix_aion_incident_runs_status", "status"),
    Index("ix_aion_incident_runs_mode", "mode"),
    Index("ix_aion_incident_runs_created_at", "created_at"),
)

aion_root_cause_candidates = Table(
    "aion_root_cause_candidates",
    incident_metadata,
    Column("root_cause_candidate_id", Text, primary_key=True),
    Column("incident_id", Text, nullable=False),
    Column("trace_id", Text, nullable=True),
    Column("status", Text, nullable=False),
    Column("candidate_type", Text, nullable=False),
    Column("severity", Text, nullable=False),
    Column("title", Text, nullable=False),
    Column("hypothesis", Text, nullable=False),
    Column("confidence", Float, nullable=False),
    Column("supporting_refs", json_payload_type, nullable=False),
    Column("opposing_refs", json_payload_type, nullable=False),
    Column("missing_evidence", json_payload_type, nullable=False),
    Column("recommended_checks", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    Column("confirmed_at", DateTime(timezone=True), nullable=True),
    Column("dismissed_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_root_causes_incident_id", "incident_id"),
    Index("ix_aion_root_causes_trace_id", "trace_id"),
    Index("ix_aion_root_causes_status", "status"),
    Index("ix_aion_root_causes_candidate_type", "candidate_type"),
    Index("ix_aion_root_causes_severity", "severity"),
    Index("ix_aion_root_causes_created_at", "created_at"),
)

aion_recovery_review_records = Table(
    "aion_recovery_review_records",
    incident_metadata,
    Column("recovery_review_id", Text, primary_key=True),
    Column("incident_id", Text, nullable=False),
    Column("trace_id", Text, nullable=True),
    Column("status", Text, nullable=False),
    Column("review_type", Text, nullable=False),
    Column("title", Text, nullable=False),
    Column("summary", Text, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("findings", json_payload_type, nullable=False),
    Column("recommendations", json_payload_type, nullable=False),
    Column("action_proposal_refs", json_payload_type, nullable=False),
    Column("compensation_plan_refs", json_payload_type, nullable=False),
    Column("notification_refs", json_payload_type, nullable=False),
    Column("outcome_refs", json_payload_type, nullable=False),
    Column("created_records", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    Index("ix_aion_recovery_reviews_incident_id", "incident_id"),
    Index("ix_aion_recovery_reviews_trace_id", "trace_id"),
    Index("ix_aion_recovery_reviews_status", "status"),
    Index("ix_aion_recovery_reviews_review_type", "review_type"),
    Index("ix_aion_recovery_reviews_created_at", "created_at"),
)


class IncidentRepository:
    """Repository for incident-owned records."""

    def __init__(
        self,
        database_url: str | None = None,
        *,
        engine: Engine | None = None,
        auto_create: bool = True,
    ) -> None:
        if engine is None:
            if database_url is None:
                raise ValueError("database_url or engine is required")
            if database_url.startswith("sqlite"):
                self._engine = create_engine(
                    database_url,
                    connect_args={"check_same_thread": False},
                    poolclass=StaticPool,
                )
            else:
                self._engine = create_engine(database_url, poolclass=QueuePool, pool_pre_ping=True)
        else:
            self._engine = engine
        self._auto_create = auto_create
        self._schema_ready = False

    def save_signal(self, signal: IncidentSignal) -> IncidentSignal:
        now = datetime.now(UTC)
        stored = signal.model_copy(update={"created_at": signal.created_at or now})
        self._replace(
            aion_incident_signals,
            "incident_signal_id",
            stored.incident_signal_id,
            stored,
        )
        return stored

    def get_signal(self, incident_signal_id: str) -> IncidentSignal | None:
        return self._get(
            aion_incident_signals,
            "incident_signal_id",
            incident_signal_id,
            _row_to_signal,
        )

    def list_signals(
        self,
        *,
        scope: list[str] | None = None,
        status: str | None = None,
        source_type: str | None = None,
        signal_type: str | None = None,
        severity: str | None = None,
        trace_id: str | None = None,
        source_id: str | None = None,
        correlation_key: str | None = None,
        since: datetime | None = None,
        until: datetime | None = None,
        include_deleted: bool = False,
        limit: int = 100,
    ) -> list[IncidentSignal]:
        self._ensure_schema()
        statement = (
            select(aion_incident_signals)
            .order_by(aion_incident_signals.c.occurred_at.desc())
            .limit(limit)
        )
        filters = {
            "status": status,
            "source_type": source_type,
            "signal_type": signal_type,
            "severity": severity,
            "trace_id": trace_id,
            "source_id": source_id,
            "correlation_key": correlation_key,
        }
        for column, value in filters.items():
            if value is not None:
                statement = statement.where(getattr(aion_incident_signals.c, column) == value)
        if since is not None:
            statement = statement.where(aion_incident_signals.c.occurred_at >= since)
        if until is not None:
            statement = statement.where(aion_incident_signals.c.occurred_at <= until)
        if not include_deleted:
            statement = statement.where(aion_incident_signals.c.deleted_at.is_(None))
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
        signals = [_row_to_signal(row) for row in rows]
        return _filter_scope(signals, scope)

    def link_signal(self, incident_signal_id: str, incident_id: str) -> IncidentSignal | None:
        signal = self.get_signal(incident_signal_id)
        if signal is None:
            return None
        linked = signal.model_copy(
            update={"incident_id": incident_id, "status": "linked", "linked_at": datetime.now(UTC)}
        )
        return self.save_signal(linked)

    def save_incident(self, incident: IncidentRecord) -> IncidentRecord:
        now = datetime.now(UTC)
        stored = incident.model_copy(
            update={"created_at": incident.created_at or now, "updated_at": now}
        )
        self._replace(aion_incident_records, "incident_id", stored.incident_id, stored)
        return stored

    def get_incident(self, incident_id: str) -> IncidentRecord | None:
        return self._get(aion_incident_records, "incident_id", incident_id, _row_to_incident)

    def list_incidents(
        self, query: IncidentQuery | None = None, *, limit: int = 100
    ) -> list[IncidentRecord]:
        self._ensure_schema()
        statement = (
            select(aion_incident_records)
            .order_by(aion_incident_records.c.created_at.desc())
            .limit(query.limit if query is not None else limit)
        )
        if query is not None:
            filters = {
                "trace_id": query.trace_id,
                "status": query.status,
                "incident_type": query.incident_type,
                "severity": query.severity,
                "correlation_key": query.correlation_key,
            }
            for column, value in filters.items():
                if value is not None:
                    statement = statement.where(getattr(aion_incident_records.c, column) == value)
            if not query.include_deleted:
                statement = statement.where(aion_incident_records.c.deleted_at.is_(None))
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
        incidents = [_row_to_incident(row) for row in rows]
        if query is not None:
            incidents = _filter_scope(incidents, query.scope)
        return incidents

    def save_rule(self, rule: IncidentCorrelationRule) -> IncidentCorrelationRule:
        now = datetime.now(UTC)
        stored = rule.model_copy(update={"created_at": rule.created_at or now, "updated_at": now})
        self._replace(
            aion_incident_correlation_rules,
            "correlation_rule_id",
            stored.correlation_rule_id,
            stored,
        )
        return stored

    def get_rule(self, correlation_rule_id: str) -> IncidentCorrelationRule | None:
        return self._get(
            aion_incident_correlation_rules,
            "correlation_rule_id",
            correlation_rule_id,
            _row_to_rule,
        )

    def list_rules(
        self,
        *,
        scope: list[str] | None = None,
        status: str | None = None,
        rule_type: str | None = None,
        limit: int = 100,
    ) -> list[IncidentCorrelationRule]:
        self._ensure_schema()
        statement = (
            select(aion_incident_correlation_rules)
            .order_by(aion_incident_correlation_rules.c.created_at.desc())
            .limit(limit)
        )
        if status is not None:
            statement = statement.where(aion_incident_correlation_rules.c.status == status)
        if rule_type is not None:
            statement = statement.where(aion_incident_correlation_rules.c.rule_type == rule_type)
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
        return _filter_scope([_row_to_rule(row) for row in rows], scope)

    def save_correlation_run(self, run: IncidentCorrelationRun) -> IncidentCorrelationRun:
        now = datetime.now(UTC)
        stored = run.model_copy(
            update={"created_at": run.created_at or now, "completed_at": run.completed_at or now}
        )
        self._replace(
            aion_incident_correlation_runs,
            "correlation_run_id",
            stored.correlation_run_id,
            stored,
        )
        return stored

    def get_correlation_run(self, correlation_run_id: str) -> IncidentCorrelationRun | None:
        return self._get(
            aion_incident_correlation_runs,
            "correlation_run_id",
            correlation_run_id,
            _row_to_run,
        )

    def save_root_cause(self, candidate: RootCauseCandidate) -> RootCauseCandidate:
        now = datetime.now(UTC)
        stored = candidate.model_copy(
            update={"created_at": candidate.created_at or now, "updated_at": now}
        )
        self._replace(
            aion_root_cause_candidates,
            "root_cause_candidate_id",
            stored.root_cause_candidate_id,
            stored,
        )
        incident = self.get_incident(stored.incident_id)
        if incident and stored.root_cause_candidate_id not in incident.root_cause_candidate_refs:
            self.save_incident(
                incident.model_copy(
                    update={
                        "root_cause_candidate_refs": [
                            *incident.root_cause_candidate_refs,
                            stored.root_cause_candidate_id,
                        ]
                    }
                )
            )
        return stored

    def get_root_cause(self, root_cause_candidate_id: str) -> RootCauseCandidate | None:
        return self._get(
            aion_root_cause_candidates,
            "root_cause_candidate_id",
            root_cause_candidate_id,
            _row_to_root_cause,
        )

    def list_root_causes(
        self,
        *,
        incident_id: str | None = None,
        status: str | None = None,
        candidate_type: str | None = None,
        limit: int = 100,
    ) -> list[RootCauseCandidate]:
        self._ensure_schema()
        statement = (
            select(aion_root_cause_candidates)
            .order_by(aion_root_cause_candidates.c.created_at.desc())
            .limit(limit)
        )
        if incident_id is not None:
            statement = statement.where(aion_root_cause_candidates.c.incident_id == incident_id)
        if status is not None:
            statement = statement.where(aion_root_cause_candidates.c.status == status)
        if candidate_type is not None:
            statement = statement.where(
                aion_root_cause_candidates.c.candidate_type == candidate_type
            )
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
        return [_row_to_root_cause(row) for row in rows]

    def save_recovery_review(self, review: RecoveryReview) -> RecoveryReview:
        now = datetime.now(UTC)
        stored = review.model_copy(
            update={"created_at": review.created_at or now, "updated_at": now}
        )
        self._replace(
            aion_recovery_review_records,
            "recovery_review_id",
            stored.recovery_review_id,
            stored,
        )
        incident = self.get_incident(stored.incident_id)
        if incident and stored.recovery_review_id not in incident.recovery_review_refs:
            self.save_incident(
                incident.model_copy(
                    update={
                        "recovery_review_refs": [
                            *incident.recovery_review_refs,
                            stored.recovery_review_id,
                        ]
                    }
                )
            )
        return stored

    def get_recovery_review(self, recovery_review_id: str) -> RecoveryReview | None:
        return self._get(
            aion_recovery_review_records,
            "recovery_review_id",
            recovery_review_id,
            _row_to_recovery_review,
        )

    def list_recovery_reviews(
        self,
        *,
        scope: list[str] | None = None,
        incident_id: str | None = None,
        status: str | None = None,
        limit: int = 100,
    ) -> list[RecoveryReview]:
        self._ensure_schema()
        statement = (
            select(aion_recovery_review_records)
            .order_by(aion_recovery_review_records.c.created_at.desc())
            .limit(limit)
        )
        if incident_id is not None:
            statement = statement.where(aion_recovery_review_records.c.incident_id == incident_id)
        if status is not None:
            statement = statement.where(aion_recovery_review_records.c.status == status)
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
        return _filter_scope([_row_to_recovery_review(row) for row in rows], scope)

    def _replace(self, table: Table, key_column: str, key_value: str, model: Any) -> None:
        self._ensure_schema()
        values = _table_values(table, model)
        with self._engine.begin() as connection:
            existing = connection.execute(
                select(table.c[key_column]).where(table.c[key_column] == key_value)
            ).first()
            if existing is None:
                connection.execute(insert(table).values(**values))
            else:
                connection.execute(
                    update(table).where(table.c[key_column] == key_value).values(**values)
                )

    def _get(self, table: Table, key_column: str, key_value: str, mapper: Any) -> Any | None:
        self._ensure_schema()
        with self._engine.connect() as connection:
            row = (
                connection.execute(select(table).where(table.c[key_column] == key_value))
                .mappings()
                .first()
            )
        return mapper(row) if row is not None else None

    def _ensure_schema(self) -> None:
        if self._schema_ready or not self._auto_create:
            return
        incident_metadata.create_all(self._engine)
        self._schema_ready = True


def _table_values(table: Table, model: Any) -> dict[str, Any]:
    python_data = model.model_dump(mode="python")
    json_data = model.model_dump(mode="json")
    values: dict[str, Any] = {}
    for column in table.columns:
        if column.name not in python_data:
            continue
        value = python_data[column.name]
        values[column.name] = json_data[column.name] if isinstance(value, (dict, list)) else value
    return values


def _row_to_signal(row: RowMapping) -> IncidentSignal:
    return IncidentSignal(**dict(row))


def _row_to_incident(row: RowMapping) -> IncidentRecord:
    return IncidentRecord(**dict(row))


def _row_to_rule(row: RowMapping) -> IncidentCorrelationRule:
    return IncidentCorrelationRule(**dict(row))


def _row_to_run(row: RowMapping) -> IncidentCorrelationRun:
    data = dict(row)
    data["incidents"] = [IncidentRecord(**item) for item in data.get("incidents", [])]
    return IncidentCorrelationRun(**data)


def _row_to_root_cause(row: RowMapping) -> RootCauseCandidate:
    return RootCauseCandidate(**dict(row))


def _row_to_recovery_review(row: RowMapping) -> RecoveryReview:
    return RecoveryReview(**dict(row))


def _filter_scope(items: list[Any], scope: list[str] | None) -> list[Any]:
    if not scope:
        return items
    scope_set = set(scope)
    return [
        item
        for item in items
        if bool(scope_set.intersection(set(getattr(item, "owner_scope", []) or [])))
    ]


__all__ = [
    "IncidentRepository",
    "aion_incident_correlation_rules",
    "aion_incident_correlation_runs",
    "aion_incident_records",
    "aion_incident_signals",
    "aion_recovery_review_records",
    "aion_root_cause_candidates",
    "incident_metadata",
]
