"""Persistent repository for lifecycle-owned records."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, cast

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
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

from aion_brain.contracts.lifecycle import (
    ArchiveCandidate,
    LifecycleEvaluationRun,
    LifecycleReport,
    LifecycleReviewRecord,
    PurgePreview,
    RedactionCandidate,
)
from aion_brain.contracts.retention import LifecyclePolicy, RetentionClassification

lifecycle_metadata = MetaData()
json_payload_type = JSON().with_variant(JSONB(), "postgresql")


aion_lifecycle_policies = Table(
    "aion_lifecycle_policies",
    lifecycle_metadata,
    Column("lifecycle_policy_id", Text, primary_key=True),
    Column("name", Text, nullable=False, unique=True),
    Column("description", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("policy_type", Text, nullable=False),
    Column("resource_types", json_payload_type, nullable=False),
    Column("source_systems", json_payload_type, nullable=False),
    Column("retention_class", Text, nullable=False),
    Column("retention_days", Integer, nullable=False),
    Column("review_after_days", Integer, nullable=True),
    Column("archive_after_days", Integer, nullable=True),
    Column("purge_after_days", Integer, nullable=True),
    Column("action_on_match", Text, nullable=False),
    Column("requires_backup", Boolean, nullable=False),
    Column("requires_approval", Boolean, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("rule", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    Column("disabled_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_lifecycle_policies_name", "name"),
    Index("ix_aion_lifecycle_policies_status", "status"),
    Index("ix_aion_lifecycle_policies_type", "policy_type"),
    Index("ix_aion_lifecycle_policies_class", "retention_class"),
    Index("ix_aion_lifecycle_policies_action", "action_on_match"),
    Index("ix_aion_lifecycle_policies_backup", "requires_backup"),
    Index("ix_aion_lifecycle_policies_approval", "requires_approval"),
    Index("ix_aion_lifecycle_policies_created_at", "created_at"),
)

aion_retention_classifications = Table(
    "aion_retention_classifications",
    lifecycle_metadata,
    Column("classification_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("resource_uri", Text, nullable=False),
    Column("resource_type", Text, nullable=False),
    Column("resource_id", Text, nullable=False),
    Column("source_system", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("retention_class", Text, nullable=False),
    Column("lifecycle_state", Text, nullable=False),
    Column("sensitivity", Text, nullable=False),
    Column("policy_refs", json_payload_type, nullable=False),
    Column("reasons", json_payload_type, nullable=False),
    Column("retention_until", DateTime(timezone=True), nullable=True),
    Column("review_after", DateTime(timezone=True), nullable=True),
    Column("archive_after", DateTime(timezone=True), nullable=True),
    Column("purge_after", DateTime(timezone=True), nullable=True),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    Column("deleted_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_retention_classifications_trace", "trace_id"),
    Index("ix_aion_retention_classifications_uri", "resource_uri"),
    Index("ix_aion_retention_classifications_type", "resource_type"),
    Index("ix_aion_retention_classifications_resource_id", "resource_id"),
    Index("ix_aion_retention_classifications_source", "source_system"),
    Index("ix_aion_retention_classifications_status", "status"),
    Index("ix_aion_retention_classifications_class", "retention_class"),
    Index("ix_aion_retention_classifications_state", "lifecycle_state"),
    Index("ix_aion_retention_classifications_sensitivity", "sensitivity"),
    Index("ix_aion_retention_classifications_retention_until", "retention_until"),
    Index("ix_aion_retention_classifications_review_after", "review_after"),
    Index("ix_aion_retention_classifications_archive_after", "archive_after"),
    Index("ix_aion_retention_classifications_purge_after", "purge_after"),
    Index("ix_aion_retention_classifications_created_at", "created_at"),
    Index("ix_aion_retention_classifications_deleted_at", "deleted_at"),
)

aion_lifecycle_evaluation_runs = Table(
    "aion_lifecycle_evaluation_runs",
    lifecycle_metadata,
    Column("lifecycle_evaluation_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("actor_id", Text, nullable=True),
    Column("workspace_id", Text, nullable=True),
    Column("status", Text, nullable=False),
    Column("mode", Text, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("resource_types", json_payload_type, nullable=False),
    Column("source_systems", json_payload_type, nullable=False),
    Column("policy_ids", json_payload_type, nullable=False),
    Column("resources_evaluated", Integer, nullable=False),
    Column("classifications_created", Integer, nullable=False),
    Column("archive_candidates_created", Integer, nullable=False),
    Column("redaction_candidates_created", Integer, nullable=False),
    Column("purge_previews_created", Integer, nullable=False),
    Column("reviews_created", Integer, nullable=False),
    Column("classifications", json_payload_type, nullable=False),
    Column("archive_candidates", json_payload_type, nullable=False),
    Column("redaction_candidates", json_payload_type, nullable=False),
    Column("purge_previews", json_payload_type, nullable=False),
    Column("review_records", json_payload_type, nullable=False),
    Column("warnings", json_payload_type, nullable=False),
    Column("failures", json_payload_type, nullable=False),
    Column("result", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("completed_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_lifecycle_runs_trace", "trace_id"),
    Index("ix_aion_lifecycle_runs_actor", "actor_id"),
    Index("ix_aion_lifecycle_runs_workspace", "workspace_id"),
    Index("ix_aion_lifecycle_runs_status", "status"),
    Index("ix_aion_lifecycle_runs_mode", "mode"),
    Index("ix_aion_lifecycle_runs_evaluated", "resources_evaluated"),
    Index("ix_aion_lifecycle_runs_classifications_created", "classifications_created"),
    Index("ix_aion_lifecycle_runs_archive_created", "archive_candidates_created"),
    Index("ix_aion_lifecycle_runs_redaction_created", "redaction_candidates_created"),
    Index("ix_aion_lifecycle_runs_purge_created", "purge_previews_created"),
    Index("ix_aion_lifecycle_runs_reviews_created", "reviews_created"),
    Index("ix_aion_lifecycle_runs_created_at", "created_at"),
)

aion_archive_candidates = Table(
    "aion_archive_candidates",
    lifecycle_metadata,
    Column("archive_candidate_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("resource_uri", Text, nullable=False),
    Column("resource_type", Text, nullable=False),
    Column("resource_id", Text, nullable=False),
    Column("source_system", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("severity", Text, nullable=False),
    Column("reason", Text, nullable=False),
    Column("lifecycle_policy_id", Text, nullable=True),
    Column("classification_id", Text, nullable=True),
    Column("backup_required", Boolean, nullable=False),
    Column("backup_verified", Boolean, nullable=False),
    Column("action_proposal_id", Text, nullable=True),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("reviewed_at", DateTime(timezone=True), nullable=True),
    Column("dismissed_at", DateTime(timezone=True), nullable=True),
    Column("converted_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_archive_candidates_trace", "trace_id"),
    Index("ix_aion_archive_candidates_uri", "resource_uri"),
    Index("ix_aion_archive_candidates_type", "resource_type"),
    Index("ix_aion_archive_candidates_resource_id", "resource_id"),
    Index("ix_aion_archive_candidates_source", "source_system"),
    Index("ix_aion_archive_candidates_status", "status"),
    Index("ix_aion_archive_candidates_severity", "severity"),
    Index("ix_aion_archive_candidates_policy", "lifecycle_policy_id"),
    Index("ix_aion_archive_candidates_backup_required", "backup_required"),
    Index("ix_aion_archive_candidates_backup_verified", "backup_verified"),
    Index("ix_aion_archive_candidates_action_proposal", "action_proposal_id"),
    Index("ix_aion_archive_candidates_created_at", "created_at"),
)

aion_redaction_candidates = Table(
    "aion_redaction_candidates",
    lifecycle_metadata,
    Column("redaction_candidate_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("resource_uri", Text, nullable=False),
    Column("resource_type", Text, nullable=False),
    Column("resource_id", Text, nullable=False),
    Column("source_system", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("severity", Text, nullable=False),
    Column("reason", Text, nullable=False),
    Column("sensitive_paths", json_payload_type, nullable=False),
    Column("suggested_redaction_mode", Text, nullable=False),
    Column("lifecycle_policy_id", Text, nullable=True),
    Column("classification_id", Text, nullable=True),
    Column("action_proposal_id", Text, nullable=True),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("reviewed_at", DateTime(timezone=True), nullable=True),
    Column("dismissed_at", DateTime(timezone=True), nullable=True),
    Column("converted_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_redaction_candidates_trace", "trace_id"),
    Index("ix_aion_redaction_candidates_uri", "resource_uri"),
    Index("ix_aion_redaction_candidates_type", "resource_type"),
    Index("ix_aion_redaction_candidates_resource_id", "resource_id"),
    Index("ix_aion_redaction_candidates_source", "source_system"),
    Index("ix_aion_redaction_candidates_status", "status"),
    Index("ix_aion_redaction_candidates_severity", "severity"),
    Index("ix_aion_redaction_candidates_mode", "suggested_redaction_mode"),
    Index("ix_aion_redaction_candidates_policy", "lifecycle_policy_id"),
    Index("ix_aion_redaction_candidates_action_proposal", "action_proposal_id"),
    Index("ix_aion_redaction_candidates_created_at", "created_at"),
)

aion_purge_previews = Table(
    "aion_purge_previews",
    lifecycle_metadata,
    Column("purge_preview_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("status", Text, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("resource_uris", json_payload_type, nullable=False),
    Column("resource_count", Integer, nullable=False),
    Column("blocked_count", Integer, nullable=False),
    Column("allowed_count", Integer, nullable=False),
    Column("blockers", json_payload_type, nullable=False),
    Column("warnings", json_payload_type, nullable=False),
    Column("estimated_impact", json_payload_type, nullable=False),
    Column("requires_backup", Boolean, nullable=False),
    Column("backup_verified", Boolean, nullable=False),
    Column("hard_delete_allowed", Boolean, nullable=False),
    Column("result", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Index("ix_aion_purge_previews_trace", "trace_id"),
    Index("ix_aion_purge_previews_status", "status"),
    Index("ix_aion_purge_previews_resource_count", "resource_count"),
    Index("ix_aion_purge_previews_blocked_count", "blocked_count"),
    Index("ix_aion_purge_previews_allowed_count", "allowed_count"),
    Index("ix_aion_purge_previews_backup_required", "requires_backup"),
    Index("ix_aion_purge_previews_backup_verified", "backup_verified"),
    Index("ix_aion_purge_previews_hard_delete", "hard_delete_allowed"),
    Index("ix_aion_purge_previews_created_at", "created_at"),
)

aion_lifecycle_review_records = Table(
    "aion_lifecycle_review_records",
    lifecycle_metadata,
    Column("lifecycle_review_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("resource_uri", Text, nullable=True),
    Column("candidate_type", Text, nullable=False),
    Column("candidate_id", Text, nullable=True),
    Column("status", Text, nullable=False),
    Column("decision", Text, nullable=False),
    Column("actor_id", Text, nullable=True),
    Column("workspace_id", Text, nullable=True),
    Column("reason", Text, nullable=False),
    Column("policy_decision_id", Text, nullable=True),
    Column("approval_request_id", Text, nullable=True),
    Column("action_proposal_id", Text, nullable=True),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Index("ix_aion_lifecycle_reviews_trace", "trace_id"),
    Index("ix_aion_lifecycle_reviews_uri", "resource_uri"),
    Index("ix_aion_lifecycle_reviews_candidate_type", "candidate_type"),
    Index("ix_aion_lifecycle_reviews_candidate_id", "candidate_id"),
    Index("ix_aion_lifecycle_reviews_status", "status"),
    Index("ix_aion_lifecycle_reviews_decision", "decision"),
    Index("ix_aion_lifecycle_reviews_actor", "actor_id"),
    Index("ix_aion_lifecycle_reviews_workspace", "workspace_id"),
    Index("ix_aion_lifecycle_reviews_action_proposal", "action_proposal_id"),
    Index("ix_aion_lifecycle_reviews_created_at", "created_at"),
)

aion_lifecycle_reports = Table(
    "aion_lifecycle_reports",
    lifecycle_metadata,
    Column("lifecycle_report_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("status", Text, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("resource_count", Integer, nullable=False),
    Column("classified_count", Integer, nullable=False),
    Column("archive_candidate_count", Integer, nullable=False),
    Column("redaction_candidate_count", Integer, nullable=False),
    Column("purge_preview_count", Integer, nullable=False),
    Column("overdue_review_count", Integer, nullable=False),
    Column("sensitive_resource_count", Integer, nullable=False),
    Column("findings", json_payload_type, nullable=False),
    Column("recommendations", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Index("ix_aion_lifecycle_reports_trace", "trace_id"),
    Index("ix_aion_lifecycle_reports_status", "status"),
    Index("ix_aion_lifecycle_reports_resource_count", "resource_count"),
    Index("ix_aion_lifecycle_reports_classified_count", "classified_count"),
    Index("ix_aion_lifecycle_reports_archive_count", "archive_candidate_count"),
    Index("ix_aion_lifecycle_reports_redaction_count", "redaction_candidate_count"),
    Index("ix_aion_lifecycle_reports_overdue_count", "overdue_review_count"),
    Index("ix_aion_lifecycle_reports_created_at", "created_at"),
)


class LifecycleRepository:
    """Repository for lifecycle-owned records only."""

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

    def save_policy(self, policy: LifecyclePolicy) -> LifecyclePolicy:
        now = datetime.now(UTC)
        stored = policy.model_copy(
            update={"created_at": policy.created_at or now, "updated_at": now}
        )
        self._replace(
            aion_lifecycle_policies,
            "lifecycle_policy_id",
            stored.lifecycle_policy_id,
            _model_values(aion_lifecycle_policies, stored),
        )
        return stored

    def get_policy(self, lifecycle_policy_id: str) -> LifecyclePolicy | None:
        return self._get(
            aion_lifecycle_policies,
            "lifecycle_policy_id",
            lifecycle_policy_id,
            lambda row: LifecyclePolicy(**dict(row)),
        )

    def list_policies(
        self,
        scope: list[str],
        *,
        status: str | None = None,
        policy_type: str | None = None,
        retention_class: str | None = None,
        limit: int = 100,
    ) -> list[LifecyclePolicy]:
        rows = self._list(
            aion_lifecycle_policies,
            LifecyclePolicy,
            status=status,
            policy_type=policy_type,
            retention_class=retention_class,
            limit=limit,
        )
        return _filter_scope(rows, scope)

    def save_classification(
        self, classification: RetentionClassification
    ) -> RetentionClassification:
        now = datetime.now(UTC)
        stored = classification.model_copy(
            update={
                "created_at": classification.created_at or now,
                "updated_at": now,
            }
        )
        self._replace(
            aion_retention_classifications,
            "classification_id",
            stored.classification_id,
            _model_values(aion_retention_classifications, stored),
        )
        return stored

    def get_classification_by_uri(
        self, resource_uri: str, scope: list[str]
    ) -> RetentionClassification | None:
        self._ensure_schema()
        with self._engine.connect() as connection:
            row = (
                connection.execute(
                    select(aion_retention_classifications)
                    .where(aion_retention_classifications.c.resource_uri == resource_uri)
                    .where(aion_retention_classifications.c.deleted_at.is_(None))
                )
                .mappings()
                .first()
            )
        item = RetentionClassification(**dict(row)) if row is not None else None
        return item if item is not None and _scope_matches(item.owner_scope, scope) else None

    def list_classifications(
        self,
        scope: list[str],
        *,
        retention_class: str | None = None,
        lifecycle_state: str | None = None,
        limit: int = 100,
    ) -> list[RetentionClassification]:
        rows = self._list(
            aion_retention_classifications,
            RetentionClassification,
            retention_class=retention_class,
            lifecycle_state=lifecycle_state,
            limit=limit,
        )
        return _filter_scope(rows, scope)

    def save_evaluation_run(self, run: LifecycleEvaluationRun) -> LifecycleEvaluationRun:
        now = datetime.now(UTC)
        stored = run.model_copy(
            update={"created_at": run.created_at or now, "completed_at": run.completed_at or now}
        )
        self._replace(
            aion_lifecycle_evaluation_runs,
            "lifecycle_evaluation_id",
            stored.lifecycle_evaluation_id,
            _model_values(aion_lifecycle_evaluation_runs, stored),
        )
        return stored

    def get_evaluation_run(self, lifecycle_evaluation_id: str) -> LifecycleEvaluationRun | None:
        return self._get(
            aion_lifecycle_evaluation_runs,
            "lifecycle_evaluation_id",
            lifecycle_evaluation_id,
            _row_to_evaluation_run,
        )

    def save_archive_candidate(self, candidate: ArchiveCandidate) -> ArchiveCandidate:
        return cast(
            ArchiveCandidate,
            self._save_model(
                aion_archive_candidates,
                "archive_candidate_id",
                candidate.archive_candidate_id,
                candidate,
            ),
        )

    def get_archive_candidate(self, archive_candidate_id: str) -> ArchiveCandidate | None:
        return self._get(
            aion_archive_candidates,
            "archive_candidate_id",
            archive_candidate_id,
            lambda row: ArchiveCandidate(**dict(row)),
        )

    def list_archive_candidates(
        self,
        scope: list[str],
        *,
        status: str | None = None,
        severity: str | None = None,
        limit: int = 100,
    ) -> list[ArchiveCandidate]:
        rows = self._list(
            aion_archive_candidates,
            ArchiveCandidate,
            status=status,
            severity=severity,
            limit=limit,
        )
        return _filter_scope(rows, scope)

    def save_redaction_candidate(self, candidate: RedactionCandidate) -> RedactionCandidate:
        return cast(
            RedactionCandidate,
            self._save_model(
                aion_redaction_candidates,
                "redaction_candidate_id",
                candidate.redaction_candidate_id,
                candidate,
            ),
        )

    def get_redaction_candidate(self, redaction_candidate_id: str) -> RedactionCandidate | None:
        return self._get(
            aion_redaction_candidates,
            "redaction_candidate_id",
            redaction_candidate_id,
            lambda row: RedactionCandidate(**dict(row)),
        )

    def list_redaction_candidates(
        self,
        scope: list[str],
        *,
        status: str | None = None,
        severity: str | None = None,
        limit: int = 100,
    ) -> list[RedactionCandidate]:
        rows = self._list(
            aion_redaction_candidates,
            RedactionCandidate,
            status=status,
            severity=severity,
            limit=limit,
        )
        return _filter_scope(rows, scope)

    def save_purge_preview(self, preview: PurgePreview) -> PurgePreview:
        return cast(
            PurgePreview,
            self._save_model(
                aion_purge_previews,
                "purge_preview_id",
                preview.purge_preview_id,
                preview,
            ),
        )

    def get_purge_preview(self, purge_preview_id: str) -> PurgePreview | None:
        return self._get(
            aion_purge_previews,
            "purge_preview_id",
            purge_preview_id,
            lambda row: PurgePreview(**dict(row)),
        )

    def list_purge_previews(
        self,
        scope: list[str],
        *,
        status: str | None = None,
        limit: int = 100,
    ) -> list[PurgePreview]:
        rows = self._list(aion_purge_previews, PurgePreview, status=status, limit=limit)
        return _filter_scope(rows, scope)

    def save_review(self, review: LifecycleReviewRecord) -> LifecycleReviewRecord:
        return cast(
            LifecycleReviewRecord,
            self._save_model(
                aion_lifecycle_review_records,
                "lifecycle_review_id",
                review.lifecycle_review_id,
                review,
            ),
        )

    def list_reviews(
        self,
        scope: list[str],
        *,
        candidate_type: str | None = None,
        decision: str | None = None,
        limit: int = 100,
    ) -> list[LifecycleReviewRecord]:
        rows = self._list(
            aion_lifecycle_review_records,
            LifecycleReviewRecord,
            candidate_type=candidate_type,
            decision=decision,
            limit=limit,
        )
        return _filter_scope(rows, scope)

    def save_report(self, report: LifecycleReport) -> LifecycleReport:
        return cast(
            LifecycleReport,
            self._save_model(
                aion_lifecycle_reports,
                "lifecycle_report_id",
                report.lifecycle_report_id,
                report,
            ),
        )

    def list_reports(self, scope: list[str], limit: int = 100) -> list[LifecycleReport]:
        rows = self._list(aion_lifecycle_reports, LifecycleReport, limit=limit)
        return _filter_scope(rows, scope)

    def latest_report(self, scope: list[str]) -> LifecycleReport | None:
        reports = self.list_reports(scope, limit=1)
        return reports[0] if reports else None

    def _save_model(self, table: Table, key_column: str, key_value: str, model: Any) -> Any:
        stored = model.model_copy(update={"created_at": model.created_at or datetime.now(UTC)})
        self._replace(table, key_column, key_value, _model_values(table, stored))
        return stored

    def _list(self, table: Table, model: Any, *, limit: int = 100, **filters: Any) -> list[Any]:
        self._ensure_schema()
        statement = select(table).order_by(table.c.created_at.desc()).limit(limit)
        for column, value in filters.items():
            if value is not None:
                statement = statement.where(getattr(table.c, column) == value)
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
        return [model(**dict(row)) for row in rows]

    def _replace(
        self, table: Table, key_column: str, key_value: str, values: dict[str, Any]
    ) -> None:
        self._ensure_schema()
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
        lifecycle_metadata.create_all(self._engine)
        self._schema_ready = True


def _model_values(table: Table, model: Any) -> dict[str, Any]:
    python_data = model.model_dump(mode="python")
    json_data = model.model_dump(mode="json")
    values: dict[str, Any] = {}
    for column in table.columns:
        if column.name not in python_data:
            continue
        value = python_data[column.name]
        values[column.name] = json_data[column.name] if isinstance(value, (dict, list)) else value
    return values


def _row_to_evaluation_run(row: RowMapping) -> LifecycleEvaluationRun:
    data = dict(row)
    data["classifications"] = [
        RetentionClassification(**item) for item in data.get("classifications", [])
    ]
    data["archive_candidates"] = [
        ArchiveCandidate(**item) for item in data.get("archive_candidates", [])
    ]
    data["redaction_candidates"] = [
        RedactionCandidate(**item) for item in data.get("redaction_candidates", [])
    ]
    data["purge_previews"] = [PurgePreview(**item) for item in data.get("purge_previews", [])]
    data["review_records"] = [
        LifecycleReviewRecord(**item) for item in data.get("review_records", [])
    ]
    return LifecycleEvaluationRun(**data)


def _filter_scope(items: list[Any], scope: list[str]) -> list[Any]:
    return [item for item in items if _scope_matches(getattr(item, "owner_scope", []), scope)]


def _scope_matches(owner_scope: list[str], scope: list[str]) -> bool:
    return bool(set(owner_scope).intersection(scope))


__all__ = [
    "LifecycleRepository",
    "aion_archive_candidates",
    "aion_lifecycle_evaluation_runs",
    "aion_lifecycle_policies",
    "aion_lifecycle_reports",
    "aion_lifecycle_review_records",
    "aion_purge_previews",
    "aion_redaction_candidates",
    "aion_retention_classifications",
]
