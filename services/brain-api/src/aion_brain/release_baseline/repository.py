"""Persistence for release baseline reports."""

from datetime import datetime
from typing import cast

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    Index,
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

from aion_brain.contracts.release_baseline import ReleaseBaselineReport, ReleaseBaselineStatus

release_baseline_metadata = MetaData()
json_payload_type = JSON().with_variant(JSONB(), "postgresql")

aion_release_baseline_reports = Table(
    "aion_release_baseline_reports",
    release_baseline_metadata,
    Column("release_baseline_id", Text, primary_key=True),
    Column("version", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("scenario_run_ids", json_payload_type, nullable=False),
    Column("quality_gate_results", json_payload_type, nullable=False),
    Column("report", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("completed_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_release_baseline_reports_version", "version"),
    Index("ix_aion_release_baseline_reports_status", "status"),
    Index("ix_aion_release_baseline_reports_created_at", "created_at"),
)


class ReleaseBaselineRepository:
    """Store deterministic release baseline reports."""

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

    def save(self, report: ReleaseBaselineReport) -> ReleaseBaselineReport:
        """Persist one report."""
        self._ensure_schema()
        with self._engine.begin() as connection:
            connection.execute(
                delete(aion_release_baseline_reports).where(
                    aion_release_baseline_reports.c.release_baseline_id
                    == report.release_baseline_id
                )
            )
            connection.execute(
                insert(aion_release_baseline_reports).values(**report.model_dump(mode="python"))
            )
        return report

    def get(self, release_baseline_id: str) -> ReleaseBaselineReport | None:
        """Return one report by ID."""
        self._ensure_schema()
        statement = select(aion_release_baseline_reports).where(
            aion_release_baseline_reports.c.release_baseline_id == release_baseline_id
        )
        with self._engine.connect() as connection:
            row = connection.execute(statement).mappings().first()
        return _row_to_report(row) if row is not None else None

    def list(
        self,
        *,
        version: str | None = None,
        status: str | None = None,
        limit: int = 50,
    ) -> list[ReleaseBaselineReport]:
        """List recent reports."""
        self._ensure_schema()
        statement = select(aion_release_baseline_reports)
        if version:
            statement = statement.where(aion_release_baseline_reports.c.version == version)
        if status:
            statement = statement.where(aion_release_baseline_reports.c.status == status)
        statement = statement.order_by(aion_release_baseline_reports.c.created_at.desc()).limit(
            limit
        )
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
        return [_row_to_report(row) for row in rows]

    def _ensure_schema(self) -> None:
        if self._schema_ready or not self._auto_create:
            return
        release_baseline_metadata.create_all(self._engine)
        self._schema_ready = True


def _row_to_report(row: RowMapping) -> ReleaseBaselineReport:
    return ReleaseBaselineReport(
        release_baseline_id=str(row["release_baseline_id"]),
        version=str(row["version"]),
        status=cast(ReleaseBaselineStatus, str(row["status"])),
        scenario_run_ids=_string_list(row["scenario_run_ids"]),
        quality_gate_results=dict(row["quality_gate_results"]),
        report=dict(row["report"]),
        created_by=_optional_str(row["created_by"]),
        created_at=_datetime(row["created_at"]),
        completed_at=_optional_datetime(row["completed_at"]),
    )


def _optional_str(value: object) -> str | None:
    return None if value is None else str(value)


def _datetime(value: object) -> datetime:
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(str(value))


def _optional_datetime(value: object) -> datetime | None:
    return None if value is None else _datetime(value)


def _string_list(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value]
    return []
