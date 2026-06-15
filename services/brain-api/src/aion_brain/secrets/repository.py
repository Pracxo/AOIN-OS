"""Persistent repository for metadata-only secret references."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, cast

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
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
from sqlalchemy.pool import QueuePool

from aion_brain.contracts.secrets import (
    SecretProvider,
    SecretRef,
    SecretRefStatus,
    SecretSensitivity,
    SecretType,
)

secret_metadata = MetaData()
json_payload_type = JSON().with_variant(JSONB(), "postgresql")

aion_secret_refs = Table(
    "aion_secret_refs",
    secret_metadata,
    Column("secret_ref_id", Text, primary_key=True),
    Column("name", Text, nullable=False),
    Column("description", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("secret_type", Text, nullable=False),
    Column("provider", Text, nullable=False),
    Column("external_ref", Text, nullable=True),
    Column("sensitivity", Text, nullable=False),
    Column("rotation_policy", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    Column("disabled_at", DateTime(timezone=True), nullable=True),
    Column("last_rotated_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_secret_refs_name", "name"),
    Index("ix_aion_secret_refs_status", "status"),
    Index("ix_aion_secret_refs_secret_type", "secret_type"),
    Index("ix_aion_secret_refs_provider", "provider"),
    Index("ix_aion_secret_refs_sensitivity", "sensitivity"),
    Index("ix_aion_secret_refs_created_at", "created_at"),
)


class SecretRefRepository:
    """Repository for metadata-only secret references."""

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

    def save(self, secret_ref: SecretRef) -> SecretRef:
        """Upsert one secret reference."""
        self._ensure_schema()
        now = datetime.now(UTC)
        values = secret_ref.model_dump(mode="python")
        values["created_at"] = values["created_at"] or now
        values["updated_at"] = now
        stored = secret_ref.model_copy(
            update={"created_at": values["created_at"], "updated_at": values["updated_at"]}
        )
        with self._engine.begin() as connection:
            existing = connection.execute(
                select(aion_secret_refs.c.secret_ref_id).where(
                    aion_secret_refs.c.secret_ref_id == secret_ref.secret_ref_id
                )
            ).first()
            if existing is None:
                connection.execute(insert(aion_secret_refs).values(**values))
            else:
                connection.execute(
                    update(aion_secret_refs)
                    .where(aion_secret_refs.c.secret_ref_id == secret_ref.secret_ref_id)
                    .values(**values)
                )
        return stored

    def get(self, secret_ref_id: str) -> SecretRef | None:
        """Return one secret reference."""
        self._ensure_schema()
        with self._engine.connect() as connection:
            row = connection.execute(
                select(aion_secret_refs).where(aion_secret_refs.c.secret_ref_id == secret_ref_id)
            ).mappings().first()
        return _row_to_secret(row) if row is not None else None

    def list(self, status: str | None = None) -> list[SecretRef]:
        """List secret references."""
        self._ensure_schema()
        statement = select(aion_secret_refs)
        if status is not None:
            statement = statement.where(aion_secret_refs.c.status == status)
        statement = statement.order_by(aion_secret_refs.c.created_at)
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
        return [_row_to_secret(row) for row in rows]

    def _ensure_schema(self) -> None:
        if self._schema_ready:
            return
        if self._auto_create:
            secret_metadata.create_all(self._engine)
        self._schema_ready = True


def _row_to_secret(row: RowMapping) -> SecretRef:
    return SecretRef(
        secret_ref_id=str(row["secret_ref_id"]),
        name=str(row["name"]),
        description=str(row["description"]),
        status=cast(SecretRefStatus, str(row["status"])),
        owner_scope=list(row["owner_scope"]),
        secret_type=cast(SecretType, str(row["secret_type"])),
        provider=cast(SecretProvider, str(row["provider"])),
        external_ref=_optional_str(row["external_ref"]),
        sensitivity=cast(SecretSensitivity, str(row["sensitivity"])),
        rotation_policy=dict(row["rotation_policy"]),
        metadata=dict(row["metadata"]),
        created_by=_optional_str(row["created_by"]),
        created_at=_optional_datetime(row["created_at"]),
        updated_at=_optional_datetime(row["updated_at"]),
        disabled_at=_optional_datetime(row["disabled_at"]),
        last_rotated_at=_optional_datetime(row["last_rotated_at"]),
    )


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def _optional_datetime(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo is not None else value.replace(tzinfo=UTC)
    if isinstance(value, str):
        return datetime.fromisoformat(value)
    raise TypeError(f"expected datetime-compatible value, got {type(value)!r}")


__all__ = ["SecretRefRepository", "aion_secret_refs", "secret_metadata"]
