"""Persistent repository for module developer kit records."""

from datetime import UTC, datetime
from typing import Any, cast

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    MetaData,
    Table,
    Text,
    UniqueConstraint,
    create_engine,
    insert,
    select,
    update,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.engine import Engine, RowMapping
from sqlalchemy.pool import QueuePool

from aion_brain.contracts.capabilities import CapabilityManifest
from aion_brain.contracts.module_developer import (
    CapabilityCertification,
    CapabilityCertificationCheck,
    CertificationStatus,
    ModuleCertificationRun,
    ModuleContractTestCase,
    ModulePackage,
    ModulePackageStatus,
)

module_developer_metadata = MetaData()
json_payload_type = JSON().with_variant(JSONB(), "postgresql")

aion_module_packages = Table(
    "aion_module_packages",
    module_developer_metadata,
    Column("module_package_id", Text, primary_key=True),
    Column("module_id", Text, nullable=False),
    Column("version", Text, nullable=False),
    Column("package_name", Text, nullable=False),
    Column("display_name", Text, nullable=False),
    Column("description", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("manifest", json_payload_type, nullable=False),
    Column("compatibility", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    Column("disabled_at", DateTime(timezone=True), nullable=True),
    UniqueConstraint("module_id", "version", name="uq_aion_module_packages_module_version"),
    Index("ix_aion_module_packages_module_id", "module_id"),
    Index("ix_aion_module_packages_version", "version"),
    Index("ix_aion_module_packages_package_name", "package_name"),
    Index("ix_aion_module_packages_status", "status"),
    Index("ix_aion_module_packages_created_at", "created_at"),
)

aion_capability_certifications = Table(
    "aion_capability_certifications",
    module_developer_metadata,
    Column("certification_id", Text, primary_key=True),
    Column(
        "module_package_id",
        Text,
        ForeignKey("aion_module_packages.module_package_id"),
        nullable=False,
    ),
    Column("module_id", Text, nullable=False),
    Column("version", Text, nullable=False),
    Column("capability_id", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("score", Float, nullable=False),
    Column("checks", json_payload_type, nullable=False),
    Column("failures", json_payload_type, nullable=False),
    Column("warnings", json_payload_type, nullable=False),
    Column("certified_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Index("ix_aion_capability_certifications_package", "module_package_id"),
    Index("ix_aion_capability_certifications_module_id", "module_id"),
    Index("ix_aion_capability_certifications_version", "version"),
    Index("ix_aion_capability_certifications_capability_id", "capability_id"),
    Index("ix_aion_capability_certifications_status", "status"),
    Index("ix_aion_capability_certifications_score", "score"),
    Index("ix_aion_capability_certifications_created_at", "created_at"),
)

aion_module_certification_runs = Table(
    "aion_module_certification_runs",
    module_developer_metadata,
    Column("certification_run_id", Text, primary_key=True),
    Column(
        "module_package_id",
        Text,
        ForeignKey("aion_module_packages.module_package_id"),
        nullable=False,
    ),
    Column("module_id", Text, nullable=False),
    Column("version", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("total_checks", Integer, nullable=False),
    Column("passed_checks", Integer, nullable=False),
    Column("failed_checks", Integer, nullable=False),
    Column("warning_checks", Integer, nullable=False),
    Column("score", Float, nullable=False),
    Column("report", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("completed_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_module_certification_runs_package", "module_package_id"),
    Index("ix_aion_module_certification_runs_module_id", "module_id"),
    Index("ix_aion_module_certification_runs_version", "version"),
    Index("ix_aion_module_certification_runs_status", "status"),
    Index("ix_aion_module_certification_runs_score", "score"),
    Index("ix_aion_module_certification_runs_created_at", "created_at"),
)

aion_module_contract_test_cases = Table(
    "aion_module_contract_test_cases",
    module_developer_metadata,
    Column("test_case_id", Text, primary_key=True),
    Column("module_package_id", Text, nullable=True),
    Column("capability_id", Text, nullable=True),
    Column("test_type", Text, nullable=False),
    Column("name", Text, nullable=False),
    Column("description", Text, nullable=False),
    Column("input", json_payload_type, nullable=False),
    Column("expected", json_payload_type, nullable=False),
    Column("status", Text, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Index("ix_aion_module_contract_test_cases_package", "module_package_id"),
    Index("ix_aion_module_contract_test_cases_capability_id", "capability_id"),
    Index("ix_aion_module_contract_test_cases_test_type", "test_type"),
    Index("ix_aion_module_contract_test_cases_status", "status"),
    Index("ix_aion_module_contract_test_cases_created_at", "created_at"),
)


class ModuleDeveloperRepository:
    """Repository for module package certification records."""

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

    def save_package(self, package: ModulePackage) -> ModulePackage:
        """Upsert a module package."""
        self._ensure_schema()
        now = datetime.now(UTC)
        values = package.model_dump(mode="python")
        values["manifest"] = package.manifest.model_dump(mode="python")
        values["created_at"] = values["created_at"] or now
        values["updated_at"] = now
        stored = package.model_copy(
            update={"created_at": values["created_at"], "updated_at": values["updated_at"]}
        )
        with self._engine.begin() as connection:
            existing = connection.execute(
                select(aion_module_packages.c.module_package_id).where(
                    aion_module_packages.c.module_package_id == package.module_package_id
                )
            ).first()
            if existing is None:
                connection.execute(insert(aion_module_packages).values(**values))
            else:
                connection.execute(
                    update(aion_module_packages)
                    .where(aion_module_packages.c.module_package_id == package.module_package_id)
                    .values(**values)
                )
        return stored

    def get_package(self, module_package_id: str) -> ModulePackage | None:
        """Return one module package."""
        self._ensure_schema()
        with self._engine.connect() as connection:
            row = connection.execute(
                select(aion_module_packages).where(
                    aion_module_packages.c.module_package_id == module_package_id
                )
            ).mappings().first()
        return _row_to_package(row) if row is not None else None

    def list_packages(
        self,
        *,
        status: str | None = None,
        module_id: str | None = None,
    ) -> list[ModulePackage]:
        """List module packages."""
        self._ensure_schema()
        statement = select(aion_module_packages)
        if status is not None:
            statement = statement.where(aion_module_packages.c.status == status)
        if module_id is not None:
            statement = statement.where(aion_module_packages.c.module_id == module_id)
        statement = statement.order_by(aion_module_packages.c.created_at)
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
        return [_row_to_package(row) for row in rows]

    def save_certification(
        self,
        certification: CapabilityCertification,
    ) -> CapabilityCertification:
        """Persist one capability certification."""
        self._ensure_schema()
        values = certification.model_dump(mode="python")
        values["checks"] = [check.model_dump(mode="python") for check in certification.checks]
        values["created_at"] = values["created_at"] or datetime.now(UTC)
        stored = certification.model_copy(update={"created_at": values["created_at"]})
        with self._engine.begin() as connection:
            connection.execute(insert(aion_capability_certifications).values(**values))
        return stored

    def save_certification_run(self, run: ModuleCertificationRun) -> ModuleCertificationRun:
        """Persist one module certification run."""
        self._ensure_schema()
        values = run.model_dump(mode="python")
        values["created_at"] = values["created_at"] or datetime.now(UTC)
        stored = run.model_copy(update={"created_at": values["created_at"]})
        with self._engine.begin() as connection:
            connection.execute(insert(aion_module_certification_runs).values(**values))
        return stored

    def get_certification_run(self, certification_run_id: str) -> ModuleCertificationRun | None:
        """Return one certification run."""
        self._ensure_schema()
        with self._engine.connect() as connection:
            row = connection.execute(
                select(aion_module_certification_runs).where(
                    aion_module_certification_runs.c.certification_run_id
                    == certification_run_id
                )
            ).mappings().first()
        return _row_to_run(row) if row is not None else None

    def list_certification_runs(
        self,
        *,
        module_package_id: str | None = None,
    ) -> list[ModuleCertificationRun]:
        """List certification runs."""
        self._ensure_schema()
        statement = select(aion_module_certification_runs)
        if module_package_id is not None:
            statement = statement.where(
                aion_module_certification_runs.c.module_package_id == module_package_id
            )
        statement = statement.order_by(aion_module_certification_runs.c.created_at)
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
        return [_row_to_run(row) for row in rows]

    def save_contract_test_case(
        self,
        test_case: ModuleContractTestCase,
    ) -> ModuleContractTestCase:
        """Persist one contract test case."""
        self._ensure_schema()
        values = test_case.model_dump(mode="python")
        values["created_at"] = values["created_at"] or datetime.now(UTC)
        stored = test_case.model_copy(update={"created_at": values["created_at"]})
        with self._engine.begin() as connection:
            connection.execute(insert(aion_module_contract_test_cases).values(**values))
        return stored

    def _ensure_schema(self) -> None:
        if self._schema_ready or not self._auto_create:
            return
        module_developer_metadata.create_all(self._engine)
        self._schema_ready = True


def _row_to_package(row: RowMapping) -> ModulePackage:
    return ModulePackage(
        module_package_id=str(row["module_package_id"]),
        module_id=str(row["module_id"]),
        version=str(row["version"]),
        package_name=str(row["package_name"]),
        display_name=str(row["display_name"]),
        description=str(row["description"]),
        status=cast(ModulePackageStatus, str(row["status"])),
        manifest=CapabilityManifest.model_validate(row["manifest"]),
        compatibility=dict(row["compatibility"]),
        metadata=dict(row["metadata"]),
        created_by=_optional_str(row["created_by"]),
        created_at=_optional_datetime(row["created_at"]),
        updated_at=_optional_datetime(row["updated_at"]),
        disabled_at=_optional_datetime(row["disabled_at"]),
    )


def _row_to_run(row: RowMapping) -> ModuleCertificationRun:
    return ModuleCertificationRun(
        certification_run_id=str(row["certification_run_id"]),
        module_package_id=str(row["module_package_id"]),
        module_id=str(row["module_id"]),
        version=str(row["version"]),
        status=cast(CertificationStatus, str(row["status"])),
        total_checks=int(row["total_checks"]),
        passed_checks=int(row["passed_checks"]),
        failed_checks=int(row["failed_checks"]),
        warning_checks=int(row["warning_checks"]),
        score=float(row["score"]),
        report=dict(row["report"]),
        created_by=_optional_str(row["created_by"]),
        created_at=_optional_datetime(row["created_at"]),
        completed_at=_optional_datetime(row["completed_at"]),
    )


def _row_to_certification(row: RowMapping) -> CapabilityCertification:
    return CapabilityCertification(
        certification_id=str(row["certification_id"]),
        module_package_id=str(row["module_package_id"]),
        module_id=str(row["module_id"]),
        version=str(row["version"]),
        capability_id=str(row["capability_id"]),
        status=cast(CertificationStatus, str(row["status"])),
        score=float(row["score"]),
        checks=[CapabilityCertificationCheck.model_validate(item) for item in list(row["checks"])],
        failures=list(row["failures"]),
        warnings=list(row["warnings"]),
        certified_by=_optional_str(row["certified_by"]),
        created_at=_optional_datetime(row["created_at"]),
    )


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def _optional_datetime(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value
    if isinstance(value, str):
        return datetime.fromisoformat(value)
    raise TypeError(f"expected datetime-compatible value, got {type(value)!r}")


__all__ = [
    "ModuleDeveloperRepository",
    "aion_capability_certifications",
    "aion_module_certification_runs",
    "aion_module_contract_test_cases",
    "aion_module_packages",
    "module_developer_metadata",
]
