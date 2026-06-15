"""Persistence for local security baseline records."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

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
    UniqueConstraint,
    create_engine,
    delete,
    insert,
    select,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.engine import Engine, RowMapping
from sqlalchemy.pool import QueuePool, StaticPool

from aion_brain.contracts.security_baseline import (
    AttackSurfaceRecord,
    HardeningGateRun,
    SecretScanFinding,
    SecurityControlRecord,
    SecurityScanRun,
    ThreatModelRecord,
)

security_metadata = MetaData()
json_payload_type = JSON().with_variant(JSONB(), "postgresql")

aion_threat_model_records = Table(
    "aion_threat_model_records",
    security_metadata,
    Column("threat_model_id", Text, primary_key=True),
    Column("name", Text, nullable=False),
    Column("description", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("category", Text, nullable=False),
    Column("asset_type", Text, nullable=False),
    Column("threat_type", Text, nullable=False),
    Column("severity", Text, nullable=False),
    Column("likelihood", Text, nullable=False),
    Column("impact", Text, nullable=False),
    Column("controls", json_payload_type, nullable=False),
    Column("residual_risk", Text, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    Column("resolved_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_threat_model_records_status", "status"),
    Index("ix_aion_threat_model_records_category", "category"),
    Index("ix_aion_threat_model_records_asset_type", "asset_type"),
    Index("ix_aion_threat_model_records_threat_type", "threat_type"),
    Index("ix_aion_threat_model_records_severity", "severity"),
    Index("ix_aion_threat_model_records_likelihood", "likelihood"),
    Index("ix_aion_threat_model_records_residual_risk", "residual_risk"),
    Index("ix_aion_threat_model_records_created_at", "created_at"),
)

aion_attack_surface_records = Table(
    "aion_attack_surface_records",
    security_metadata,
    Column("attack_surface_id", Text, primary_key=True),
    Column("surface_type", Text, nullable=False),
    Column("name", Text, nullable=False),
    Column("description", Text, nullable=False),
    Column("exposure_level", Text, nullable=False),
    Column("risk_level", Text, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("controls", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    Index("ix_aion_attack_surface_records_surface_type", "surface_type"),
    Index("ix_aion_attack_surface_records_exposure_level", "exposure_level"),
    Index("ix_aion_attack_surface_records_risk_level", "risk_level"),
    Index("ix_aion_attack_surface_records_created_at", "created_at"),
)

aion_security_control_records = Table(
    "aion_security_control_records",
    security_metadata,
    Column("security_control_id", Text, primary_key=True),
    Column("control_key", Text, nullable=False),
    Column("name", Text, nullable=False),
    Column("description", Text, nullable=False),
    Column("category", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("required", Boolean, nullable=False),
    Column("evidence_refs", json_payload_type, nullable=False),
    Column("implementation_refs", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    UniqueConstraint("control_key", name="uq_aion_security_control_records_control_key"),
    Index("ix_aion_security_control_records_control_key", "control_key"),
    Index("ix_aion_security_control_records_category", "category"),
    Index("ix_aion_security_control_records_status", "status"),
    Index("ix_aion_security_control_records_required", "required"),
    Index("ix_aion_security_control_records_created_at", "created_at"),
)

aion_secret_scan_findings = Table(
    "aion_secret_scan_findings",
    security_metadata,
    Column("finding_id", Text, primary_key=True),
    Column("scan_id", Text, nullable=False),
    Column("file_path", Text, nullable=False),
    Column("line_number", Integer, nullable=True),
    Column("finding_type", Text, nullable=False),
    Column("severity", Text, nullable=False),
    Column("redacted_match", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("reason", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Index("ix_aion_secret_scan_findings_scan_id", "scan_id"),
    Index("ix_aion_secret_scan_findings_file_path", "file_path"),
    Index("ix_aion_secret_scan_findings_finding_type", "finding_type"),
    Index("ix_aion_secret_scan_findings_severity", "severity"),
    Index("ix_aion_secret_scan_findings_status", "status"),
    Index("ix_aion_secret_scan_findings_created_at", "created_at"),
)

aion_security_scan_runs = Table(
    "aion_security_scan_runs",
    security_metadata,
    Column("security_scan_id", Text, primary_key=True),
    Column("scan_type", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("checks", json_payload_type, nullable=False),
    Column("findings", json_payload_type, nullable=False),
    Column("failures", json_payload_type, nullable=False),
    Column("warnings", json_payload_type, nullable=False),
    Column("report", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("completed_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_security_scan_runs_scan_type", "scan_type"),
    Index("ix_aion_security_scan_runs_status", "status"),
    Index("ix_aion_security_scan_runs_created_at", "created_at"),
)

aion_hardening_gate_runs = Table(
    "aion_hardening_gate_runs",
    security_metadata,
    Column("hardening_gate_id", Text, primary_key=True),
    Column("version", Text, nullable=True),
    Column("status", Text, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("checks", json_payload_type, nullable=False),
    Column("failures", json_payload_type, nullable=False),
    Column("warnings", json_payload_type, nullable=False),
    Column("report", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("completed_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_hardening_gate_runs_version", "version"),
    Index("ix_aion_hardening_gate_runs_status", "status"),
    Index("ix_aion_hardening_gate_runs_created_at", "created_at"),
)


class SecurityBaselineRepository:
    """Store local security baseline records."""

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
            if database_url.startswith("sqlite") and ":memory:" in database_url:
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

    def save_threat_model(self, record: ThreatModelRecord) -> ThreatModelRecord:
        self._ensure_schema()
        now = datetime.now(UTC)
        values = record.model_dump(mode="json", exclude={"created_at", "updated_at", "resolved_at"})
        values["created_at"] = record.created_at or now
        values["updated_at"] = record.updated_at or now
        values["resolved_at"] = record.resolved_at
        with self._engine.begin() as connection:
            connection.execute(
                delete(aion_threat_model_records).where(
                    aion_threat_model_records.c.threat_model_id == record.threat_model_id
                )
            )
            connection.execute(insert(aion_threat_model_records).values(**values))
        return record.model_copy(
            update={
                "created_at": values["created_at"],
                "updated_at": values["updated_at"],
                "resolved_at": values["resolved_at"],
            }
        )

    def get_threat_model(self, threat_model_id: str) -> ThreatModelRecord | None:
        self._ensure_schema()
        statement = select(aion_threat_model_records).where(
            aion_threat_model_records.c.threat_model_id == threat_model_id
        )
        with self._engine.connect() as connection:
            row = connection.execute(statement).mappings().first()
        return _row_to_threat_model(row) if row else None

    def list_threat_models(
        self,
        *,
        status: str | None = None,
        category: str | None = None,
    ) -> list[ThreatModelRecord]:
        self._ensure_schema()
        statement = select(aion_threat_model_records).order_by(
            aion_threat_model_records.c.created_at.desc()
        )
        if status:
            statement = statement.where(aion_threat_model_records.c.status == status)
        if category:
            statement = statement.where(aion_threat_model_records.c.category == category)
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
        return [_row_to_threat_model(row) for row in rows]

    def save_attack_surface(self, record: AttackSurfaceRecord) -> AttackSurfaceRecord:
        self._ensure_schema()
        now = datetime.now(UTC)
        values = record.model_dump(mode="json", exclude={"created_at", "updated_at"})
        values["created_at"] = record.created_at or now
        values["updated_at"] = record.updated_at or now
        with self._engine.begin() as connection:
            connection.execute(
                delete(aion_attack_surface_records).where(
                    aion_attack_surface_records.c.attack_surface_id == record.attack_surface_id
                )
            )
            connection.execute(insert(aion_attack_surface_records).values(**values))
        return record.model_copy(
            update={"created_at": values["created_at"], "updated_at": values["updated_at"]}
        )

    def save_control(self, record: SecurityControlRecord) -> SecurityControlRecord:
        self._ensure_schema()
        now = datetime.now(UTC)
        values = record.model_dump(mode="json", exclude={"created_at", "updated_at"})
        values["created_at"] = record.created_at or now
        values["updated_at"] = record.updated_at or now
        with self._engine.begin() as connection:
            connection.execute(
                delete(aion_security_control_records).where(
                    aion_security_control_records.c.control_key == record.control_key
                )
            )
            connection.execute(insert(aion_security_control_records).values(**values))
        return record.model_copy(
            update={"created_at": values["created_at"], "updated_at": values["updated_at"]}
        )

    def get_control(self, control_key: str) -> SecurityControlRecord | None:
        self._ensure_schema()
        statement = select(aion_security_control_records).where(
            aion_security_control_records.c.control_key == control_key
        )
        with self._engine.connect() as connection:
            row = connection.execute(statement).mappings().first()
        return _row_to_control(row) if row else None

    def list_controls(
        self,
        *,
        status: str | None = None,
        category: str | None = None,
    ) -> list[SecurityControlRecord]:
        self._ensure_schema()
        statement = select(aion_security_control_records).order_by(
            aion_security_control_records.c.created_at.desc()
        )
        if status:
            statement = statement.where(aion_security_control_records.c.status == status)
        if category:
            statement = statement.where(aion_security_control_records.c.category == category)
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
        return [_row_to_control(row) for row in rows]

    def save_scan(self, run: SecurityScanRun) -> SecurityScanRun:
        self._ensure_schema()
        now = datetime.now(UTC)
        values = run.model_dump(mode="json", exclude={"created_at", "completed_at"})
        values["created_at"] = run.created_at or now
        values["completed_at"] = run.completed_at
        with self._engine.begin() as connection:
            connection.execute(
                delete(aion_security_scan_runs).where(
                    aion_security_scan_runs.c.security_scan_id == run.security_scan_id
                )
            )
            connection.execute(insert(aion_security_scan_runs).values(**values))
            connection.execute(
                delete(aion_secret_scan_findings).where(
                    aion_secret_scan_findings.c.scan_id == run.security_scan_id
                )
            )
            for finding in run.findings:
                finding_values = finding.model_dump(mode="json", exclude={"created_at"})
                finding_values["created_at"] = finding.created_at or now
                connection.execute(insert(aion_secret_scan_findings).values(**finding_values))
        return run.model_copy(
            update={"created_at": values["created_at"], "completed_at": values["completed_at"]}
        )

    def get_scan(self, security_scan_id: str) -> SecurityScanRun | None:
        self._ensure_schema()
        statement = select(aion_security_scan_runs).where(
            aion_security_scan_runs.c.security_scan_id == security_scan_id
        )
        with self._engine.connect() as connection:
            row = connection.execute(statement).mappings().first()
        return _row_to_scan(row) if row else None

    def list_scans(
        self,
        *,
        scan_type: str | None = None,
        status: str | None = None,
    ) -> list[SecurityScanRun]:
        self._ensure_schema()
        statement = select(aion_security_scan_runs).order_by(
            aion_security_scan_runs.c.created_at.desc()
        )
        if scan_type:
            statement = statement.where(aion_security_scan_runs.c.scan_type == scan_type)
        if status:
            statement = statement.where(aion_security_scan_runs.c.status == status)
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
        return [_row_to_scan(row) for row in rows]

    def save_hardening_gate(self, run: HardeningGateRun) -> HardeningGateRun:
        self._ensure_schema()
        now = datetime.now(UTC)
        values = run.model_dump(mode="json", exclude={"created_at", "completed_at"})
        values["created_at"] = run.created_at or now
        values["completed_at"] = run.completed_at
        with self._engine.begin() as connection:
            connection.execute(
                delete(aion_hardening_gate_runs).where(
                    aion_hardening_gate_runs.c.hardening_gate_id == run.hardening_gate_id
                )
            )
            connection.execute(insert(aion_hardening_gate_runs).values(**values))
        return run.model_copy(
            update={"created_at": values["created_at"], "completed_at": values["completed_at"]}
        )

    def get_hardening_gate(self, hardening_gate_id: str) -> HardeningGateRun | None:
        self._ensure_schema()
        statement = select(aion_hardening_gate_runs).where(
            aion_hardening_gate_runs.c.hardening_gate_id == hardening_gate_id
        )
        with self._engine.connect() as connection:
            row = connection.execute(statement).mappings().first()
        return _row_to_hardening_gate(row) if row else None

    def list_hardening_gates(
        self,
        *,
        version: str | None = None,
        status: str | None = None,
    ) -> list[HardeningGateRun]:
        self._ensure_schema()
        statement = select(aion_hardening_gate_runs).order_by(
            aion_hardening_gate_runs.c.created_at.desc()
        )
        if version:
            statement = statement.where(aion_hardening_gate_runs.c.version == version)
        if status:
            statement = statement.where(aion_hardening_gate_runs.c.status == status)
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
        return [_row_to_hardening_gate(row) for row in rows]

    def _ensure_schema(self) -> None:
        if self._schema_ready or not self._auto_create:
            return
        security_metadata.create_all(self._engine)
        self._schema_ready = True


def _row_to_threat_model(row: RowMapping) -> ThreatModelRecord:
    return ThreatModelRecord(**_row_dict(row))


def _row_to_control(row: RowMapping) -> SecurityControlRecord:
    return SecurityControlRecord(**_row_dict(row))


def _row_to_scan(row: RowMapping) -> SecurityScanRun:
    data = _row_dict(row)
    data["findings"] = [
        SecretScanFinding(**finding) if isinstance(finding, dict) else finding
        for finding in data.get("findings", [])
    ]
    return SecurityScanRun(**data)


def _row_to_hardening_gate(row: RowMapping) -> HardeningGateRun:
    return HardeningGateRun(**_row_dict(row))


def _row_dict(row: RowMapping) -> dict[str, Any]:
    return {key: row[key] for key in row.keys()}
