"""Persistence for local backup and restore-preview records."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, cast

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    MetaData,
    Table,
    Text,
    create_engine,
    delete,
    insert,
    select,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.engine import Engine, RowMapping
from sqlalchemy.pool import QueuePool

from aion_brain.contracts.backups import (
    BackupFile,
    BackupJob,
    BackupJobStatus,
    BackupManifest,
    BackupRedactionMode,
    BackupResourceType,
    BackupType,
    RestoreJob,
    RestoreJobStatus,
    RestoreMode,
    RestorePreview,
    RestorePreviewStatus,
)

backup_metadata = MetaData()
json_payload_type = JSON().with_variant(JSONB(), "postgresql")

aion_backup_jobs = Table(
    "aion_backup_jobs",
    backup_metadata,
    Column("backup_job_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("actor_id", Text, nullable=True),
    Column("workspace_id", Text, nullable=True),
    Column("status", Text, nullable=False),
    Column("backup_type", Text, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("resource_types", json_payload_type, nullable=False),
    Column("redaction_mode", Text, nullable=False),
    Column("output_dir", Text, nullable=False),
    Column("manifest", json_payload_type, nullable=True),
    Column("checksums", json_payload_type, nullable=False),
    Column("result", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("completed_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_backup_jobs_trace_id", "trace_id"),
    Index("ix_aion_backup_jobs_actor_id", "actor_id"),
    Index("ix_aion_backup_jobs_workspace_id", "workspace_id"),
    Index("ix_aion_backup_jobs_status", "status"),
    Index("ix_aion_backup_jobs_backup_type", "backup_type"),
    Index("ix_aion_backup_jobs_redaction_mode", "redaction_mode"),
    Index("ix_aion_backup_jobs_created_at", "created_at"),
)

aion_backup_files = Table(
    "aion_backup_files",
    backup_metadata,
    Column("backup_file_id", Text, primary_key=True),
    Column(
        "backup_job_id",
        Text,
        ForeignKey("aion_backup_jobs.backup_job_id"),
        nullable=False,
    ),
    Column("file_path", Text, nullable=False),
    Column("resource_type", Text, nullable=False),
    Column("record_count", Integer, nullable=False),
    Column("size_bytes", Integer, nullable=False),
    Column("sha256", Text, nullable=False),
    Column("included", Boolean, nullable=False),
    Column("reason", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Index("ix_aion_backup_files_backup_job_id", "backup_job_id"),
    Index("ix_aion_backup_files_resource_type", "resource_type"),
    Index("ix_aion_backup_files_included", "included"),
    Index("ix_aion_backup_files_sha256", "sha256"),
    Index("ix_aion_backup_files_created_at", "created_at"),
)

aion_restore_previews = Table(
    "aion_restore_previews",
    backup_metadata,
    Column("restore_preview_id", Text, primary_key=True),
    Column("backup_job_id", Text, nullable=True),
    Column("trace_id", Text, nullable=True),
    Column("actor_id", Text, nullable=True),
    Column("workspace_id", Text, nullable=True),
    Column("status", Text, nullable=False),
    Column("input_manifest", json_payload_type, nullable=True),
    Column("conflict_count", Integer, nullable=False),
    Column("missing_dependency_count", Integer, nullable=False),
    Column("records_seen", Integer, nullable=False),
    Column("records_restorable", Integer, nullable=False),
    Column("records_blocked", Integer, nullable=False),
    Column("conflicts", json_payload_type, nullable=False),
    Column("plan", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("completed_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_restore_previews_backup_job_id", "backup_job_id"),
    Index("ix_aion_restore_previews_trace_id", "trace_id"),
    Index("ix_aion_restore_previews_actor_id", "actor_id"),
    Index("ix_aion_restore_previews_workspace_id", "workspace_id"),
    Index("ix_aion_restore_previews_status", "status"),
    Index("ix_aion_restore_previews_created_at", "created_at"),
)

aion_restore_jobs = Table(
    "aion_restore_jobs",
    backup_metadata,
    Column("restore_job_id", Text, primary_key=True),
    Column("restore_preview_id", Text, nullable=False),
    Column("backup_job_id", Text, nullable=True),
    Column("trace_id", Text, nullable=True),
    Column("actor_id", Text, nullable=True),
    Column("workspace_id", Text, nullable=True),
    Column("status", Text, nullable=False),
    Column("mode", Text, nullable=False),
    Column("approval_request_id", Text, nullable=True),
    Column("risk_assessment_id", Text, nullable=True),
    Column("autonomy_decision_id", Text, nullable=True),
    Column("result", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("completed_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_restore_jobs_restore_preview_id", "restore_preview_id"),
    Index("ix_aion_restore_jobs_backup_job_id", "backup_job_id"),
    Index("ix_aion_restore_jobs_trace_id", "trace_id"),
    Index("ix_aion_restore_jobs_actor_id", "actor_id"),
    Index("ix_aion_restore_jobs_workspace_id", "workspace_id"),
    Index("ix_aion_restore_jobs_status", "status"),
    Index("ix_aion_restore_jobs_mode", "mode"),
    Index("ix_aion_restore_jobs_created_at", "created_at"),
)


class BackupRepository:
    """Store backup, restore-preview, and restore job records."""

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
            self._engine = create_engine(database_url, poolclass=QueuePool, pool_pre_ping=True)
        else:
            self._engine = engine
        self._auto_create = auto_create
        self._schema_ready = False

    def save_backup_job(self, job: BackupJob) -> BackupJob:
        """Persist a backup job and its files."""
        self._ensure_schema()
        values = job.model_dump(
            mode="json",
            exclude={"files", "created_at", "completed_at"},
        )
        values["created_at"] = job.created_at
        values["completed_at"] = job.completed_at
        file_values = []
        for file in job.files:
            payload = file.model_dump(mode="json", exclude={"created_at"})
            payload["created_at"] = file.created_at
            file_values.append(payload)
        with self._engine.begin() as connection:
            connection.execute(
                delete(aion_backup_files).where(
                    aion_backup_files.c.backup_job_id == job.backup_job_id
                )
            )
            connection.execute(
                delete(aion_backup_jobs).where(
                    aion_backup_jobs.c.backup_job_id == job.backup_job_id
                )
            )
            connection.execute(insert(aion_backup_jobs).values(**values))
            if file_values:
                connection.execute(insert(aion_backup_files), file_values)
        return job

    def get_backup_job(self, backup_job_id: str) -> BackupJob | None:
        """Return one backup job."""
        self._ensure_schema()
        with self._engine.connect() as connection:
            job_row = (
                connection.execute(
                    select(aion_backup_jobs).where(
                        aion_backup_jobs.c.backup_job_id == backup_job_id
                    )
                )
                .mappings()
                .first()
            )
            file_rows = (
                connection.execute(
                    select(aion_backup_files)
                    .where(aion_backup_files.c.backup_job_id == backup_job_id)
                    .order_by(aion_backup_files.c.file_path)
                )
                .mappings()
                .all()
            )
        if job_row is None:
            return None
        return _row_to_backup_job(job_row, list(file_rows))

    def list_backup_jobs(
        self,
        *,
        workspace_id: str | None = None,
        status: str | None = None,
    ) -> list[BackupJob]:
        """List backup jobs."""
        self._ensure_schema()
        statement = select(aion_backup_jobs)
        if workspace_id:
            statement = statement.where(aion_backup_jobs.c.workspace_id == workspace_id)
        if status:
            statement = statement.where(aion_backup_jobs.c.status == status)
        statement = statement.order_by(aion_backup_jobs.c.created_at.desc())
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
        return [job for row in rows if (job := self.get_backup_job(str(row["backup_job_id"])))]

    def save_restore_preview(self, preview: RestorePreview) -> RestorePreview:
        """Persist a restore preview."""
        self._ensure_schema()
        values = preview.model_dump(
            mode="json",
            exclude={"created_at", "completed_at"},
        )
        values["created_at"] = preview.created_at
        values["completed_at"] = preview.completed_at
        with self._engine.begin() as connection:
            connection.execute(
                delete(aion_restore_previews).where(
                    aion_restore_previews.c.restore_preview_id == preview.restore_preview_id
                )
            )
            connection.execute(insert(aion_restore_previews).values(**values))
        return preview

    def get_restore_preview(self, restore_preview_id: str) -> RestorePreview | None:
        """Return one restore preview."""
        self._ensure_schema()
        with self._engine.connect() as connection:
            row = (
                connection.execute(
                    select(aion_restore_previews).where(
                        aion_restore_previews.c.restore_preview_id == restore_preview_id
                    )
                )
                .mappings()
                .first()
            )
        if row is None:
            return None
        return _row_to_restore_preview(row)

    def save_restore_job(self, job: RestoreJob) -> RestoreJob:
        """Persist a restore job."""
        self._ensure_schema()
        values = job.model_dump(mode="json", exclude={"created_at", "completed_at"})
        values["created_at"] = job.created_at
        values["completed_at"] = job.completed_at
        with self._engine.begin() as connection:
            connection.execute(
                delete(aion_restore_jobs).where(
                    aion_restore_jobs.c.restore_job_id == job.restore_job_id
                )
            )
            connection.execute(insert(aion_restore_jobs).values(**values))
        return job

    def _ensure_schema(self) -> None:
        if self._schema_ready or not self._auto_create:
            return
        backup_metadata.create_all(self._engine)
        self._schema_ready = True


def _row_to_backup_job(row: RowMapping, file_rows: list[RowMapping]) -> BackupJob:
    return BackupJob(
        backup_job_id=str(row["backup_job_id"]),
        trace_id=_optional_str(row["trace_id"]),
        actor_id=_optional_str(row["actor_id"]),
        workspace_id=_optional_str(row["workspace_id"]),
        status=cast(BackupJobStatus, str(row["status"])),
        backup_type=cast(BackupType, str(row["backup_type"])),
        owner_scope=_string_list(row["owner_scope"]),
        resource_types=[
            cast(BackupResourceType, str(item)) for item in _list(row["resource_types"])
        ],
        redaction_mode=cast(BackupRedactionMode, str(row["redaction_mode"])),
        output_dir=str(row["output_dir"]),
        manifest=(
            BackupManifest.model_validate(row["manifest"]) if row["manifest"] is not None else None
        ),
        files=[_row_to_backup_file(file_row) for file_row in file_rows],
        checksums={str(key): str(value) for key, value in dict(row["checksums"]).items()},
        result=dict(row["result"]),
        created_by=_optional_str(row["created_by"]),
        created_at=_datetime(row["created_at"]),
        completed_at=_optional_datetime(row["completed_at"]),
    )


def _row_to_backup_file(row: RowMapping) -> BackupFile:
    return BackupFile(
        backup_file_id=str(row["backup_file_id"]),
        backup_job_id=str(row["backup_job_id"]),
        file_path=str(row["file_path"]),
        resource_type=cast(BackupResourceType, str(row["resource_type"])),
        record_count=int(row["record_count"]),
        size_bytes=int(row["size_bytes"]),
        sha256=str(row["sha256"]),
        included=bool(row["included"]),
        reason=_optional_str(row["reason"]),
        created_at=_datetime(row["created_at"]),
    )


def _row_to_restore_preview(row: RowMapping) -> RestorePreview:
    return RestorePreview(
        restore_preview_id=str(row["restore_preview_id"]),
        backup_job_id=_optional_str(row["backup_job_id"]),
        trace_id=_optional_str(row["trace_id"]),
        actor_id=_optional_str(row["actor_id"]),
        workspace_id=_optional_str(row["workspace_id"]),
        status=cast(RestorePreviewStatus, str(row["status"])),
        input_manifest=(
            BackupManifest.model_validate(row["input_manifest"])
            if row["input_manifest"] is not None
            else None
        ),
        conflict_count=int(row["conflict_count"]),
        missing_dependency_count=int(row["missing_dependency_count"]),
        records_seen=int(row["records_seen"]),
        records_restorable=int(row["records_restorable"]),
        records_blocked=int(row["records_blocked"]),
        conflicts=list(row["conflicts"]),
        plan=dict(row["plan"]),
        created_by=_optional_str(row["created_by"]),
        created_at=_datetime(row["created_at"]),
        completed_at=_optional_datetime(row["completed_at"]),
    )


def _row_to_restore_job(row: RowMapping) -> RestoreJob:
    return RestoreJob(
        restore_job_id=str(row["restore_job_id"]),
        restore_preview_id=str(row["restore_preview_id"]),
        backup_job_id=_optional_str(row["backup_job_id"]),
        trace_id=_optional_str(row["trace_id"]),
        actor_id=_optional_str(row["actor_id"]),
        workspace_id=_optional_str(row["workspace_id"]),
        status=cast(RestoreJobStatus, str(row["status"])),
        mode=cast(RestoreMode, str(row["mode"])),
        approval_request_id=_optional_str(row["approval_request_id"]),
        risk_assessment_id=_optional_str(row["risk_assessment_id"]),
        autonomy_decision_id=_optional_str(row["autonomy_decision_id"]),
        result=dict(row["result"]),
        created_by=_optional_str(row["created_by"]),
        created_at=_datetime(row["created_at"]),
        completed_at=_optional_datetime(row["completed_at"]),
    )


def _optional_str(value: object) -> str | None:
    return None if value is None else str(value)


def _string_list(value: Any) -> list[str]:
    return [str(item) for item in _list(value)]


def _list(value: Any) -> list[Any]:
    return list(value) if isinstance(value, list) else []


def _datetime(value: object) -> datetime:
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=UTC)
    return datetime.fromisoformat(str(value))


def _optional_datetime(value: object) -> datetime | None:
    return None if value is None else _datetime(value)
