"""Persistence for local release package records."""

from __future__ import annotations

from datetime import datetime
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

from aion_brain.contracts.release_package import (
    ReleaseHandoffReport,
    ReleasePackage,
    ReleasePackageFile,
    ReleasePackageManifest,
    ReleasePackageStatus,
    ReleasePackageValidation,
)

release_package_metadata = MetaData()
json_payload_type = JSON().with_variant(JSONB(), "postgresql")

aion_release_packages = Table(
    "aion_release_packages",
    release_package_metadata,
    Column("release_package_id", Text, primary_key=True),
    Column("version", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("package_name", Text, nullable=False),
    Column("package_path", Text, nullable=False),
    Column("manifest", json_payload_type, nullable=False),
    Column("checksums", json_payload_type, nullable=False),
    Column("validation", json_payload_type, nullable=False),
    Column("handoff_report", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("completed_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_release_packages_version", "version"),
    Index("ix_aion_release_packages_status", "status"),
    Index("ix_aion_release_packages_package_name", "package_name"),
    Index("ix_aion_release_packages_created_at", "created_at"),
)

aion_release_package_files = Table(
    "aion_release_package_files",
    release_package_metadata,
    Column("release_package_file_id", Text, primary_key=True),
    Column(
        "release_package_id",
        Text,
        ForeignKey("aion_release_packages.release_package_id"),
        nullable=False,
    ),
    Column("file_path", Text, nullable=False),
    Column("artifact_type", Text, nullable=False),
    Column("size_bytes", Integer, nullable=False),
    Column("sha256", Text, nullable=False),
    Column("included", Boolean, nullable=False),
    Column("reason", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Index("ix_aion_release_package_files_release_package_id", "release_package_id"),
    Index("ix_aion_release_package_files_artifact_type", "artifact_type"),
    Index("ix_aion_release_package_files_included", "included"),
    Index("ix_aion_release_package_files_sha256", "sha256"),
    Index("ix_aion_release_package_files_created_at", "created_at"),
)


class ReleasePackageRepository:
    """Store local release packages and file manifests."""

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

    def save(self, package: ReleasePackage) -> ReleasePackage:
        """Persist a release package and its file records."""
        self._ensure_schema()
        values = package.model_dump(
            mode="json",
            exclude={"files", "created_at", "completed_at"},
        )
        values["created_at"] = package.created_at
        values["completed_at"] = package.completed_at
        file_values = []
        for file in package.files:
            file_payload = file.model_dump(mode="json", exclude={"created_at"})
            file_payload["created_at"] = file.created_at
            file_values.append(file_payload)
        with self._engine.begin() as connection:
            connection.execute(
                delete(aion_release_package_files).where(
                    aion_release_package_files.c.release_package_id == package.release_package_id
                )
            )
            connection.execute(
                delete(aion_release_packages).where(
                    aion_release_packages.c.release_package_id == package.release_package_id
                )
            )
            connection.execute(insert(aion_release_packages).values(**values))
            if package.files:
                connection.execute(
                    insert(aion_release_package_files),
                    file_values,
                )
        return package

    def get(self, release_package_id: str) -> ReleasePackage | None:
        """Return one package."""
        self._ensure_schema()
        statement = select(aion_release_packages).where(
            aion_release_packages.c.release_package_id == release_package_id
        )
        with self._engine.connect() as connection:
            package_row = connection.execute(statement).mappings().first()
            file_rows = (
                connection.execute(
                    select(aion_release_package_files)
                    .where(aion_release_package_files.c.release_package_id == release_package_id)
                    .order_by(aion_release_package_files.c.file_path)
                )
                .mappings()
                .all()
            )
        if package_row is None:
            return None
        return _row_to_package(package_row, list(file_rows))

    def list(
        self,
        *,
        version: str | None = None,
        status: str | None = None,
    ) -> list[ReleasePackage]:
        """List packages."""
        self._ensure_schema()
        statement = select(aion_release_packages)
        if version:
            statement = statement.where(aion_release_packages.c.version == version)
        if status:
            statement = statement.where(aion_release_packages.c.status == status)
        statement = statement.order_by(aion_release_packages.c.created_at.desc())
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
        return [package for row in rows if (package := self.get(str(row["release_package_id"])))]

    def _ensure_schema(self) -> None:
        if self._schema_ready or not self._auto_create:
            return
        release_package_metadata.create_all(self._engine)
        self._schema_ready = True


def _row_to_package(row: RowMapping, file_rows: list[RowMapping]) -> ReleasePackage:
    return ReleasePackage(
        release_package_id=str(row["release_package_id"]),
        version=str(row["version"]),
        status=cast(ReleasePackageStatus, str(row["status"])),
        package_name=str(row["package_name"]),
        package_path=str(row["package_path"]),
        manifest=ReleasePackageManifest.model_validate(row["manifest"]),
        files=[_row_to_file(file_row) for file_row in file_rows],
        checksums={str(key): str(value) for key, value in dict(row["checksums"]).items()},
        validation=ReleasePackageValidation.model_validate(row["validation"]),
        handoff_report=ReleaseHandoffReport.model_validate(row["handoff_report"]),
        created_by=_optional_str(row["created_by"]),
        created_at=_datetime(row["created_at"]),
        completed_at=_optional_datetime(row["completed_at"]),
    )


def _row_to_file(row: RowMapping) -> ReleasePackageFile:
    return ReleasePackageFile(
        release_package_file_id=str(row["release_package_file_id"]),
        release_package_id=str(row["release_package_id"]),
        file_path=str(row["file_path"]),
        artifact_type=cast(Any, str(row["artifact_type"])),
        size_bytes=int(row["size_bytes"]),
        sha256=str(row["sha256"]),
        included=bool(row["included"]),
        reason=_optional_str(row["reason"]),
        created_at=_datetime(row["created_at"]),
    )


def _optional_str(value: object) -> str | None:
    return None if value is None else str(value)


def _datetime(value: object) -> datetime:
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(str(value))


def _optional_datetime(value: object) -> datetime | None:
    return None if value is None else _datetime(value)
