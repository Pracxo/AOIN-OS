"""Persistent identity repository."""

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
    UniqueConstraint,
    create_engine,
    insert,
    select,
    update,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.engine import Engine, RowMapping
from sqlalchemy.pool import QueuePool

from aion_brain.contracts.identity import (
    ActorRecord,
    ActorStatus,
    ActorType,
    MembershipStatus,
    PermissionEffect,
    PermissionGrant,
    PermissionGrantStatus,
    ResourceType,
    WorkspaceMembership,
    WorkspaceRecord,
    WorkspaceRole,
    WorkspaceStatus,
)

identity_metadata = MetaData()
json_payload_type = JSON().with_variant(JSONB(), "postgresql")

aion_actors = Table(
    "aion_actors",
    identity_metadata,
    Column("actor_id", Text, primary_key=True),
    Column("actor_type", Text, nullable=False),
    Column("display_name", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    Column("disabled_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_actors_actor_type", "actor_type"),
    Index("ix_aion_actors_status", "status"),
    Index("ix_aion_actors_created_at", "created_at"),
)

aion_workspaces = Table(
    "aion_workspaces",
    identity_metadata,
    Column("workspace_id", Text, primary_key=True),
    Column("name", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("owner_actor_id", Text, nullable=True),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    Column("archived_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_workspaces_name", "name"),
    Index("ix_aion_workspaces_status", "status"),
    Index("ix_aion_workspaces_owner_actor_id", "owner_actor_id"),
    Index("ix_aion_workspaces_created_at", "created_at"),
)

aion_workspace_memberships = Table(
    "aion_workspace_memberships",
    identity_metadata,
    Column("membership_id", Text, primary_key=True),
    Column("workspace_id", Text, nullable=False),
    Column("actor_id", Text, nullable=False),
    Column("role", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("granted_by", Text, nullable=True),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    Column("revoked_at", DateTime(timezone=True), nullable=True),
    UniqueConstraint("workspace_id", "actor_id", name="uq_aion_workspace_actor"),
    Index("ix_aion_workspace_memberships_workspace_id", "workspace_id"),
    Index("ix_aion_workspace_memberships_actor_id", "actor_id"),
    Index("ix_aion_workspace_memberships_role", "role"),
    Index("ix_aion_workspace_memberships_status", "status"),
    Index("ix_aion_workspace_memberships_created_at", "created_at"),
)

aion_permission_grants = Table(
    "aion_permission_grants",
    identity_metadata,
    Column("grant_id", Text, primary_key=True),
    Column("actor_id", Text, nullable=True),
    Column("workspace_id", Text, nullable=True),
    Column("role", Text, nullable=True),
    Column("permission", Text, nullable=False),
    Column("resource_type", Text, nullable=False),
    Column("resource_id", Text, nullable=True),
    Column("effect", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("granted_by", Text, nullable=True),
    Column("expires_at", DateTime(timezone=True), nullable=True),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("revoked_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_permission_grants_actor_id", "actor_id"),
    Index("ix_aion_permission_grants_workspace_id", "workspace_id"),
    Index("ix_aion_permission_grants_role", "role"),
    Index("ix_aion_permission_grants_permission", "permission"),
    Index("ix_aion_permission_grants_resource_type", "resource_type"),
    Index("ix_aion_permission_grants_resource_id", "resource_id"),
    Index("ix_aion_permission_grants_effect", "effect"),
    Index("ix_aion_permission_grants_status", "status"),
    Index("ix_aion_permission_grants_expires_at", "expires_at"),
    Index("ix_aion_permission_grants_created_at", "created_at"),
)


class IdentityRepository:
    """Repository for actors, workspaces, memberships, and permission grants."""

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

    def save_actor(self, actor: ActorRecord) -> ActorRecord:
        """Upsert an actor."""
        self._ensure_schema()
        now = datetime.now(UTC)
        stored = actor.model_copy(
            update={"created_at": actor.created_at or now, "updated_at": now}
        )
        _upsert(
            self._engine,
            aion_actors,
            "actor_id",
            stored.actor_id,
            stored.model_dump(mode="python"),
        )
        return stored

    def get_actor(self, actor_id: str) -> ActorRecord | None:
        """Return an actor by ID."""
        self._ensure_schema()
        with self._engine.connect() as connection:
            row = connection.execute(
                select(aion_actors).where(aion_actors.c.actor_id == actor_id)
            ).mappings().first()
        return _row_to_actor(row) if row is not None else None

    def list_actors(self, *, status: str | None = None, limit: int = 50) -> list[ActorRecord]:
        """List actors."""
        self._ensure_schema()
        statement = select(aion_actors).order_by(aion_actors.c.created_at.desc()).limit(limit)
        if status is not None:
            statement = statement.where(aion_actors.c.status == status)
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
        return [_row_to_actor(row) for row in rows]

    def save_workspace(self, workspace: WorkspaceRecord) -> WorkspaceRecord:
        """Upsert a workspace."""
        self._ensure_schema()
        now = datetime.now(UTC)
        stored = workspace.model_copy(
            update={"created_at": workspace.created_at or now, "updated_at": now}
        )
        _upsert(
            self._engine,
            aion_workspaces,
            "workspace_id",
            stored.workspace_id,
            stored.model_dump(mode="python"),
        )
        return stored

    def get_workspace(self, workspace_id: str) -> WorkspaceRecord | None:
        """Return a workspace by ID."""
        self._ensure_schema()
        with self._engine.connect() as connection:
            row = connection.execute(
                select(aion_workspaces).where(aion_workspaces.c.workspace_id == workspace_id)
            ).mappings().first()
        return _row_to_workspace(row) if row is not None else None

    def list_workspaces(
        self,
        *,
        status: str | None = None,
        limit: int = 50,
    ) -> list[WorkspaceRecord]:
        """List workspaces."""
        self._ensure_schema()
        statement = select(aion_workspaces).order_by(
            aion_workspaces.c.created_at.desc()
        ).limit(limit)
        if status is not None:
            statement = statement.where(aion_workspaces.c.status == status)
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
        return [_row_to_workspace(row) for row in rows]

    def save_membership(self, membership: WorkspaceMembership) -> WorkspaceMembership:
        """Upsert a workspace membership."""
        self._ensure_schema()
        now = datetime.now(UTC)
        stored = membership.model_copy(
            update={"created_at": membership.created_at or now, "updated_at": now}
        )
        _upsert(
            self._engine,
            aion_workspace_memberships,
            "membership_id",
            stored.membership_id,
            stored.model_dump(mode="python"),
        )
        return stored

    def get_membership(self, workspace_id: str, actor_id: str) -> WorkspaceMembership | None:
        """Return a membership by workspace and actor."""
        self._ensure_schema()
        with self._engine.connect() as connection:
            row = connection.execute(
                select(aion_workspace_memberships).where(
                    aion_workspace_memberships.c.workspace_id == workspace_id,
                    aion_workspace_memberships.c.actor_id == actor_id,
                )
            ).mappings().first()
        return _row_to_membership(row) if row is not None else None

    def get_membership_by_id(self, membership_id: str) -> WorkspaceMembership | None:
        """Return a membership by ID."""
        self._ensure_schema()
        with self._engine.connect() as connection:
            row = connection.execute(
                select(aion_workspace_memberships).where(
                    aion_workspace_memberships.c.membership_id == membership_id
                )
            ).mappings().first()
        return _row_to_membership(row) if row is not None else None

    def list_memberships(
        self,
        *,
        workspace_id: str | None = None,
        actor_id: str | None = None,
    ) -> list[WorkspaceMembership]:
        """List workspace memberships."""
        self._ensure_schema()
        statement = select(aion_workspace_memberships).order_by(
            aion_workspace_memberships.c.created_at.desc()
        )
        if workspace_id is not None:
            statement = statement.where(aion_workspace_memberships.c.workspace_id == workspace_id)
        if actor_id is not None:
            statement = statement.where(aion_workspace_memberships.c.actor_id == actor_id)
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
        return [_row_to_membership(row) for row in rows]

    def save_permission_grant(self, grant: PermissionGrant) -> PermissionGrant:
        """Upsert a permission grant."""
        self._ensure_schema()
        stored = grant.model_copy(update={"created_at": grant.created_at or datetime.now(UTC)})
        _upsert(
            self._engine,
            aion_permission_grants,
            "grant_id",
            stored.grant_id,
            stored.model_dump(mode="python"),
        )
        return stored

    def get_permission_grant(self, grant_id: str) -> PermissionGrant | None:
        """Return a permission grant by ID."""
        self._ensure_schema()
        with self._engine.connect() as connection:
            row = connection.execute(
                select(aion_permission_grants).where(aion_permission_grants.c.grant_id == grant_id)
            ).mappings().first()
        return _row_to_grant(row) if row is not None else None

    def list_permission_grants(
        self,
        *,
        actor_id: str | None = None,
        workspace_id: str | None = None,
        role: str | None = None,
    ) -> list[PermissionGrant]:
        """List permission grants."""
        self._ensure_schema()
        statement = select(aion_permission_grants).order_by(
            aion_permission_grants.c.created_at.desc()
        )
        if actor_id is not None:
            statement = statement.where(aion_permission_grants.c.actor_id == actor_id)
        if workspace_id is not None:
            statement = statement.where(aion_permission_grants.c.workspace_id == workspace_id)
        if role is not None:
            statement = statement.where(aion_permission_grants.c.role == role)
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
        return [_row_to_grant(row) for row in rows]

    def _ensure_schema(self) -> None:
        if self._schema_ready or not self._auto_create:
            return
        identity_metadata.create_all(self._engine)
        self._schema_ready = True


def _upsert(
    engine: Engine,
    table: Table,
    key_column: str,
    key_value: str,
    values: dict[str, Any],
) -> None:
    with engine.begin() as connection:
        existing = connection.execute(
            select(table.c[key_column]).where(table.c[key_column] == key_value)
        ).first()
        if existing is None:
            connection.execute(insert(table).values(**values))
            return
        connection.execute(update(table).where(table.c[key_column] == key_value).values(**values))


def _row_to_actor(row: RowMapping) -> ActorRecord:
    return ActorRecord(
        actor_id=str(row["actor_id"]),
        actor_type=cast(ActorType, str(row["actor_type"])),
        display_name=str(row["display_name"]),
        status=cast(ActorStatus, str(row["status"])),
        metadata=dict(row["metadata"]),
        created_at=_datetime(row["created_at"]),
        updated_at=_datetime(row["updated_at"]),
        disabled_at=_optional_datetime(row["disabled_at"]),
    )


def _row_to_workspace(row: RowMapping) -> WorkspaceRecord:
    return WorkspaceRecord(
        workspace_id=str(row["workspace_id"]),
        name=str(row["name"]),
        status=cast(WorkspaceStatus, str(row["status"])),
        owner_actor_id=_optional_str(row["owner_actor_id"]),
        metadata=dict(row["metadata"]),
        created_at=_datetime(row["created_at"]),
        updated_at=_datetime(row["updated_at"]),
        archived_at=_optional_datetime(row["archived_at"]),
    )


def _row_to_membership(row: RowMapping) -> WorkspaceMembership:
    return WorkspaceMembership(
        membership_id=str(row["membership_id"]),
        workspace_id=str(row["workspace_id"]),
        actor_id=str(row["actor_id"]),
        role=cast(WorkspaceRole, str(row["role"])),
        status=cast(MembershipStatus, str(row["status"])),
        granted_by=_optional_str(row["granted_by"]),
        metadata=dict(row["metadata"]),
        created_at=_datetime(row["created_at"]),
        updated_at=_datetime(row["updated_at"]),
        revoked_at=_optional_datetime(row["revoked_at"]),
    )


def _row_to_grant(row: RowMapping) -> PermissionGrant:
    return PermissionGrant(
        grant_id=str(row["grant_id"]),
        actor_id=_optional_str(row["actor_id"]),
        workspace_id=_optional_str(row["workspace_id"]),
        role=cast(WorkspaceRole | None, _optional_str(row["role"])),
        permission=str(row["permission"]),
        resource_type=cast(ResourceType, str(row["resource_type"])),
        resource_id=_optional_str(row["resource_id"]),
        effect=cast(PermissionEffect, str(row["effect"])),
        status=cast(PermissionGrantStatus, str(row["status"])),
        granted_by=_optional_str(row["granted_by"]),
        expires_at=_optional_datetime(row["expires_at"]),
        metadata=dict(row["metadata"]),
        created_at=_datetime(row["created_at"]),
        revoked_at=_optional_datetime(row["revoked_at"]),
    )


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def _datetime(value: Any) -> datetime:
    result = _optional_datetime(value)
    if result is None:
        raise TypeError("Expected non-null datetime")
    return result


def _optional_datetime(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=UTC)
    if isinstance(value, str):
        return datetime.fromisoformat(value)
    raise TypeError(f"Expected datetime-compatible value, got {type(value)!r}")
