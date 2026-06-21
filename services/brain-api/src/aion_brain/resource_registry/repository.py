"""Persistent repository for registry-owned resource index records."""

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

from aion_brain.contracts.resource_references import (
    BrokenReference,
    OrphanedResource,
    ResourceReferenceLink,
)
from aion_brain.contracts.resource_registry import (
    ReferenceValidationRun,
    RegistryRebuildRun,
    RegistrySnapshot,
    ResourceDescriptor,
    ResourceIndexRecord,
    ResourceRegistryQuery,
)

registry_metadata = MetaData()
json_payload_type = JSON().with_variant(JSONB(), "postgresql")


aion_resource_index_records = Table(
    "aion_resource_index_records",
    registry_metadata,
    Column("resource_index_id", Text, primary_key=True),
    Column("resource_uri", Text, nullable=False),
    Column("resource_type", Text, nullable=False),
    Column("resource_id", Text, nullable=False),
    Column("trace_id", Text, nullable=True),
    Column("actor_id", Text, nullable=True),
    Column("workspace_id", Text, nullable=True),
    Column("source_system", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("visibility", Text, nullable=False),
    Column("sensitivity", Text, nullable=False),
    Column("title", Text, nullable=False),
    Column("summary", Text, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("tags", json_payload_type, nullable=False),
    Column("refs", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("content_hash", Text, nullable=True),
    Column("first_seen_at", DateTime(timezone=True), nullable=False),
    Column("last_seen_at", DateTime(timezone=True), nullable=False),
    Column("deleted_at", DateTime(timezone=True), nullable=True),
    Column("archived_at", DateTime(timezone=True), nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Index("ix_aion_resource_index_resource_uri", "resource_uri"),
    Index("ix_aion_resource_index_resource_type", "resource_type"),
    Index("ix_aion_resource_index_resource_id", "resource_id"),
    Index("ix_aion_resource_index_trace_id", "trace_id"),
    Index("ix_aion_resource_index_actor_id", "actor_id"),
    Index("ix_aion_resource_index_workspace_id", "workspace_id"),
    Index("ix_aion_resource_index_source_system", "source_system"),
    Index("ix_aion_resource_index_status", "status"),
    Index("ix_aion_resource_index_visibility", "visibility"),
    Index("ix_aion_resource_index_sensitivity", "sensitivity"),
    Index("ix_aion_resource_index_content_hash", "content_hash"),
    Index("ix_aion_resource_index_first_seen_at", "first_seen_at"),
    Index("ix_aion_resource_index_last_seen_at", "last_seen_at"),
    Index("ix_aion_resource_index_deleted_at", "deleted_at"),
)

aion_resource_reference_links = Table(
    "aion_resource_reference_links",
    registry_metadata,
    Column("resource_link_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("source_resource_uri", Text, nullable=False),
    Column("target_resource_uri", Text, nullable=False),
    Column("source_type", Text, nullable=False),
    Column("source_id", Text, nullable=False),
    Column("target_type", Text, nullable=False),
    Column("target_id", Text, nullable=False),
    Column("relation_type", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("confidence", Float, nullable=False),
    Column("discovered_by", Text, nullable=False),
    Column("evidence_refs", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("verified_at", DateTime(timezone=True), nullable=True),
    Column("broken_at", DateTime(timezone=True), nullable=True),
    Column("deleted_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_resource_links_trace_id", "trace_id"),
    Index("ix_aion_resource_links_source_uri", "source_resource_uri"),
    Index("ix_aion_resource_links_target_uri", "target_resource_uri"),
    Index("ix_aion_resource_links_source_type", "source_type"),
    Index("ix_aion_resource_links_target_type", "target_type"),
    Index("ix_aion_resource_links_relation_type", "relation_type"),
    Index("ix_aion_resource_links_status", "status"),
    Index("ix_aion_resource_links_created_at", "created_at"),
)

aion_registry_backlinks = Table(
    "aion_registry_backlinks",
    registry_metadata,
    Column("backlink_id", Text, primary_key=True),
    Column("resource_uri", Text, nullable=False),
    Column("referring_resource_uri", Text, nullable=False),
    Column("relation_type", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("deleted_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_registry_backlinks_resource_uri", "resource_uri"),
    Index("ix_aion_registry_backlinks_referring_uri", "referring_resource_uri"),
    Index("ix_aion_registry_backlinks_relation_type", "relation_type"),
    Index("ix_aion_registry_backlinks_status", "status"),
    Index("ix_aion_registry_backlinks_created_at", "created_at"),
)

aion_broken_reference_records = Table(
    "aion_broken_reference_records",
    registry_metadata,
    Column("broken_reference_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("source_resource_uri", Text, nullable=False),
    Column("target_resource_uri", Text, nullable=False),
    Column("source_type", Text, nullable=False),
    Column("source_id", Text, nullable=False),
    Column("target_type", Text, nullable=False),
    Column("target_id", Text, nullable=False),
    Column("issue_type", Text, nullable=False),
    Column("severity", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("reason", Text, nullable=False),
    Column("recommended_action", Text, nullable=False),
    Column("validation_run_id", Text, nullable=True),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("resolved_at", DateTime(timezone=True), nullable=True),
    Column("dismissed_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_broken_refs_trace_id", "trace_id"),
    Index("ix_aion_broken_refs_source_uri", "source_resource_uri"),
    Index("ix_aion_broken_refs_target_uri", "target_resource_uri"),
    Index("ix_aion_broken_refs_issue_type", "issue_type"),
    Index("ix_aion_broken_refs_severity", "severity"),
    Index("ix_aion_broken_refs_status", "status"),
    Index("ix_aion_broken_refs_validation_run_id", "validation_run_id"),
    Index("ix_aion_broken_refs_created_at", "created_at"),
)

aion_orphaned_resource_records = Table(
    "aion_orphaned_resource_records",
    registry_metadata,
    Column("orphaned_resource_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("resource_uri", Text, nullable=False),
    Column("resource_type", Text, nullable=False),
    Column("resource_id", Text, nullable=False),
    Column("source_system", Text, nullable=False),
    Column("issue_type", Text, nullable=False),
    Column("severity", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("reason", Text, nullable=False),
    Column("inbound_ref_count", Integer, nullable=False),
    Column("outbound_ref_count", Integer, nullable=False),
    Column("validation_run_id", Text, nullable=True),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("resolved_at", DateTime(timezone=True), nullable=True),
    Column("dismissed_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_orphans_trace_id", "trace_id"),
    Index("ix_aion_orphans_resource_uri", "resource_uri"),
    Index("ix_aion_orphans_resource_type", "resource_type"),
    Index("ix_aion_orphans_source_system", "source_system"),
    Index("ix_aion_orphans_issue_type", "issue_type"),
    Index("ix_aion_orphans_severity", "severity"),
    Index("ix_aion_orphans_status", "status"),
    Index("ix_aion_orphans_validation_run_id", "validation_run_id"),
)

aion_reference_validation_runs = Table(
    "aion_reference_validation_runs",
    registry_metadata,
    Column("validation_run_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("actor_id", Text, nullable=True),
    Column("workspace_id", Text, nullable=True),
    Column("status", Text, nullable=False),
    Column("mode", Text, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("resource_types", json_payload_type, nullable=False),
    Column("source_systems", json_payload_type, nullable=False),
    Column("resources_checked", Integer, nullable=False),
    Column("links_checked", Integer, nullable=False),
    Column("broken_count", Integer, nullable=False),
    Column("orphaned_count", Integer, nullable=False),
    Column("stale_count", Integer, nullable=False),
    Column("broken_references", json_payload_type, nullable=False),
    Column("orphaned_resources", json_payload_type, nullable=False),
    Column("warnings", json_payload_type, nullable=False),
    Column("failures", json_payload_type, nullable=False),
    Column("result", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("completed_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_reference_runs_trace_id", "trace_id"),
    Index("ix_aion_reference_runs_status", "status"),
    Index("ix_aion_reference_runs_mode", "mode"),
    Index("ix_aion_reference_runs_created_at", "created_at"),
)

aion_registry_rebuild_runs = Table(
    "aion_registry_rebuild_runs",
    registry_metadata,
    Column("rebuild_run_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("actor_id", Text, nullable=True),
    Column("workspace_id", Text, nullable=True),
    Column("status", Text, nullable=False),
    Column("mode", Text, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("resource_types", json_payload_type, nullable=False),
    Column("source_systems", json_payload_type, nullable=False),
    Column("resources_seen", Integer, nullable=False),
    Column("resources_indexed", Integer, nullable=False),
    Column("links_indexed", Integer, nullable=False),
    Column("skipped", Integer, nullable=False),
    Column("failures", json_payload_type, nullable=False),
    Column("warnings", json_payload_type, nullable=False),
    Column("result", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("completed_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_rebuild_runs_trace_id", "trace_id"),
    Index("ix_aion_rebuild_runs_status", "status"),
    Index("ix_aion_rebuild_runs_mode", "mode"),
    Index("ix_aion_rebuild_runs_created_at", "created_at"),
)

aion_registry_snapshots = Table(
    "aion_registry_snapshots",
    registry_metadata,
    Column("registry_snapshot_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("status", Text, nullable=False),
    Column("snapshot_type", Text, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("resource_count", Integer, nullable=False),
    Column("link_count", Integer, nullable=False),
    Column("broken_count", Integer, nullable=False),
    Column("orphaned_count", Integer, nullable=False),
    Column("resource_type_counts", json_payload_type, nullable=False),
    Column("source_system_counts", json_payload_type, nullable=False),
    Column("root_hash", Text, nullable=False),
    Column("report", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Index("ix_aion_registry_snapshots_trace_id", "trace_id"),
    Index("ix_aion_registry_snapshots_status", "status"),
    Index("ix_aion_registry_snapshots_type", "snapshot_type"),
    Index("ix_aion_registry_snapshots_root_hash", "root_hash"),
    Index("ix_aion_registry_snapshots_created_at", "created_at"),
)


class ResourceRegistryRepository:
    """Repository for registry-owned records."""

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

    def save_resource(self, record: ResourceIndexRecord) -> ResourceIndexRecord:
        now = datetime.now(UTC)
        descriptor = record.descriptor.model_copy(
            update={
                "first_seen_at": record.descriptor.first_seen_at or now,
                "last_seen_at": now,
            }
        )
        stored = record.model_copy(
            update={"descriptor": descriptor, "created_at": record.created_at or now}
        )
        self._replace(
            aion_resource_index_records,
            "resource_index_id",
            stored.resource_index_id,
            _resource_values(stored),
        )
        return stored

    def get_resource_by_uri(self, resource_uri: str) -> ResourceIndexRecord | None:
        return self._get(
            aion_resource_index_records,
            "resource_uri",
            resource_uri,
            _row_to_resource,
        )

    def get_resource_by_type_id(
        self, resource_type: str, resource_id: str
    ) -> ResourceIndexRecord | None:
        self._ensure_schema()
        with self._engine.connect() as connection:
            row = (
                connection.execute(
                    select(aion_resource_index_records)
                    .where(aion_resource_index_records.c.resource_type == resource_type)
                    .where(aion_resource_index_records.c.resource_id == resource_id)
                    .where(aion_resource_index_records.c.deleted_at.is_(None))
                )
                .mappings()
                .first()
            )
        return _row_to_resource(row) if row is not None else None

    def list_resources(
        self,
        query: ResourceRegistryQuery | None = None,
        *,
        limit: int = 100,
    ) -> list[ResourceIndexRecord]:
        self._ensure_schema()
        statement = (
            select(aion_resource_index_records)
            .order_by(aion_resource_index_records.c.last_seen_at.desc())
            .limit(query.limit if query else limit)
        )
        if query:
            filters = {
                "resource_type": query.resource_type,
                "source_system": query.source_system,
                "status": query.status,
                "trace_id": query.trace_id,
                "actor_id": query.actor_id,
                "workspace_id": query.workspace_id,
            }
            for column, value in filters.items():
                if value is not None:
                    statement = statement.where(
                        getattr(aion_resource_index_records.c, column) == value
                    )
            if query.query:
                text = f"%{query.query.lower()}%"
                statement = statement.where(
                    aion_resource_index_records.c.resource_uri.ilike(text)
                    | aion_resource_index_records.c.title.ilike(text)
                    | aion_resource_index_records.c.summary.ilike(text)
                )
            if not query.include_deleted:
                statement = statement.where(aion_resource_index_records.c.deleted_at.is_(None))
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
        resources = [_row_to_resource(row) for row in rows]
        return _filter_scope(resources, query.scope if query else None)

    def save_link(self, link: ResourceReferenceLink) -> ResourceReferenceLink:
        stored = link.model_copy(update={"created_at": link.created_at or datetime.now(UTC)})
        self._replace(
            aion_resource_reference_links,
            "resource_link_id",
            stored.resource_link_id,
            _model_values(aion_resource_reference_links, stored),
        )
        self.save_backlink(
            {
                "backlink_id": f"backlink-{stored.resource_link_id}",
                "resource_uri": stored.target_resource_uri,
                "referring_resource_uri": stored.source_resource_uri,
                "relation_type": stored.relation_type,
                "status": stored.status,
                "metadata": {"resource_link_id": stored.resource_link_id},
                "created_at": stored.created_at or datetime.now(UTC),
                "deleted_at": stored.deleted_at,
            }
        )
        return stored

    def get_link(self, resource_link_id: str) -> ResourceReferenceLink | None:
        return self._get(
            aion_resource_reference_links,
            "resource_link_id",
            resource_link_id,
            lambda row: ResourceReferenceLink(**dict(row)),
        )

    def list_links(
        self,
        *,
        source_uri: str | None = None,
        target_uri: str | None = None,
        relation_type: str | None = None,
        status: str | None = None,
        limit: int = 100,
    ) -> list[ResourceReferenceLink]:
        self._ensure_schema()
        statement = (
            select(aion_resource_reference_links)
            .order_by(aion_resource_reference_links.c.created_at.desc())
            .limit(limit)
        )
        filters = {
            "source_resource_uri": source_uri,
            "target_resource_uri": target_uri,
            "relation_type": relation_type,
            "status": status,
        }
        for column, value in filters.items():
            if value is not None:
                statement = statement.where(
                    getattr(aion_resource_reference_links.c, column) == value
                )
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
        return [ResourceReferenceLink(**dict(row)) for row in rows]

    def save_backlink(self, values: dict[str, Any]) -> dict[str, Any]:
        self._replace(aion_registry_backlinks, "backlink_id", str(values["backlink_id"]), values)
        return values

    def list_backlinks(self, resource_uri: str, limit: int = 100) -> list[dict[str, Any]]:
        self._ensure_schema()
        with self._engine.connect() as connection:
            rows = (
                connection.execute(
                    select(aion_registry_backlinks)
                    .where(aion_registry_backlinks.c.resource_uri == resource_uri)
                    .where(aion_registry_backlinks.c.deleted_at.is_(None))
                    .order_by(aion_registry_backlinks.c.created_at.desc())
                    .limit(limit)
                )
                .mappings()
                .all()
            )
        return [dict(row) for row in rows]

    def save_broken_reference(self, broken: BrokenReference) -> BrokenReference:
        stored = broken.model_copy(update={"created_at": broken.created_at or datetime.now(UTC)})
        self._replace(
            aion_broken_reference_records,
            "broken_reference_id",
            stored.broken_reference_id,
            _model_values(aion_broken_reference_records, stored),
        )
        return stored

    def list_broken_references(
        self,
        *,
        status: str | None = None,
        severity: str | None = None,
        validation_run_id: str | None = None,
        limit: int = 100,
    ) -> list[BrokenReference]:
        return self._list_integrity(
            aion_broken_reference_records,
            BrokenReference,
            status=status,
            severity=severity,
            validation_run_id=validation_run_id,
            limit=limit,
        )

    def get_broken_reference(self, broken_reference_id: str) -> BrokenReference | None:
        return self._get(
            aion_broken_reference_records,
            "broken_reference_id",
            broken_reference_id,
            lambda row: BrokenReference(**dict(row)),
        )

    def save_orphaned_resource(self, orphan: OrphanedResource) -> OrphanedResource:
        stored = orphan.model_copy(update={"created_at": orphan.created_at or datetime.now(UTC)})
        self._replace(
            aion_orphaned_resource_records,
            "orphaned_resource_id",
            stored.orphaned_resource_id,
            _model_values(aion_orphaned_resource_records, stored),
        )
        return stored

    def list_orphaned_resources(
        self,
        *,
        status: str | None = None,
        severity: str | None = None,
        validation_run_id: str | None = None,
        limit: int = 100,
    ) -> list[OrphanedResource]:
        return self._list_integrity(
            aion_orphaned_resource_records,
            OrphanedResource,
            status=status,
            severity=severity,
            validation_run_id=validation_run_id,
            limit=limit,
        )

    def get_orphaned_resource(self, orphaned_resource_id: str) -> OrphanedResource | None:
        return self._get(
            aion_orphaned_resource_records,
            "orphaned_resource_id",
            orphaned_resource_id,
            lambda row: OrphanedResource(**dict(row)),
        )

    def save_validation_run(self, run: ReferenceValidationRun) -> ReferenceValidationRun:
        stored = run.model_copy(
            update={
                "created_at": run.created_at or datetime.now(UTC),
                "completed_at": run.completed_at or datetime.now(UTC),
            }
        )
        self._replace(
            aion_reference_validation_runs,
            "validation_run_id",
            stored.validation_run_id,
            _model_values(aion_reference_validation_runs, stored),
        )
        return stored

    def get_validation_run(self, validation_run_id: str) -> ReferenceValidationRun | None:
        return self._get(
            aion_reference_validation_runs,
            "validation_run_id",
            validation_run_id,
            _row_to_validation_run,
        )

    def save_rebuild_run(self, run: RegistryRebuildRun) -> RegistryRebuildRun:
        stored = run.model_copy(
            update={
                "created_at": run.created_at or datetime.now(UTC),
                "completed_at": run.completed_at or datetime.now(UTC),
            }
        )
        self._replace(
            aion_registry_rebuild_runs,
            "rebuild_run_id",
            stored.rebuild_run_id,
            _model_values(aion_registry_rebuild_runs, stored),
        )
        return stored

    def get_rebuild_run(self, rebuild_run_id: str) -> RegistryRebuildRun | None:
        return self._get(
            aion_registry_rebuild_runs,
            "rebuild_run_id",
            rebuild_run_id,
            lambda row: RegistryRebuildRun(**dict(row)),
        )

    def list_rebuild_runs(self, limit: int = 100) -> list[RegistryRebuildRun]:
        self._ensure_schema()
        with self._engine.connect() as connection:
            rows = (
                connection.execute(
                    select(aion_registry_rebuild_runs)
                    .order_by(aion_registry_rebuild_runs.c.created_at.desc())
                    .limit(limit)
                )
                .mappings()
                .all()
            )
        return [RegistryRebuildRun(**dict(row)) for row in rows]

    def save_snapshot(self, snapshot: RegistrySnapshot) -> RegistrySnapshot:
        stored = snapshot.model_copy(
            update={"created_at": snapshot.created_at or datetime.now(UTC)}
        )
        self._replace(
            aion_registry_snapshots,
            "registry_snapshot_id",
            stored.registry_snapshot_id,
            _model_values(aion_registry_snapshots, stored),
        )
        return stored

    def get_snapshot(self, registry_snapshot_id: str) -> RegistrySnapshot | None:
        return self._get(
            aion_registry_snapshots,
            "registry_snapshot_id",
            registry_snapshot_id,
            lambda row: RegistrySnapshot(**dict(row)),
        )

    def list_snapshots(
        self,
        *,
        snapshot_type: str | None = None,
        status: str | None = None,
        limit: int = 50,
    ) -> list[RegistrySnapshot]:
        self._ensure_schema()
        statement = (
            select(aion_registry_snapshots)
            .order_by(aion_registry_snapshots.c.created_at.desc())
            .limit(limit)
        )
        if snapshot_type is not None:
            statement = statement.where(aion_registry_snapshots.c.snapshot_type == snapshot_type)
        if status is not None:
            statement = statement.where(aion_registry_snapshots.c.status == status)
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
        return [RegistrySnapshot(**dict(row)) for row in rows]

    def _list_integrity(
        self,
        table: Table,
        model: Any,
        *,
        status: str | None,
        severity: str | None,
        validation_run_id: str | None,
        limit: int,
    ) -> list[Any]:
        self._ensure_schema()
        statement = select(table).order_by(table.c.created_at.desc()).limit(limit)
        if status is not None:
            statement = statement.where(table.c.status == status)
        if severity is not None:
            statement = statement.where(table.c.severity == severity)
        if validation_run_id is not None:
            statement = statement.where(table.c.validation_run_id == validation_run_id)
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
        registry_metadata.create_all(self._engine)
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


def _resource_values(record: ResourceIndexRecord) -> dict[str, Any]:
    descriptor_python = record.descriptor.model_dump(mode="python")
    descriptor_json = record.descriptor.model_dump(mode="json")
    values = {"resource_index_id": record.resource_index_id, "created_at": record.created_at}
    for column in aion_resource_index_records.columns:
        if column.name in {"resource_index_id", "created_at"}:
            continue
        value = descriptor_python[column.name]
        values[column.name] = (
            descriptor_json[column.name] if isinstance(value, (dict, list)) else value
        )
    return values


def _row_to_resource(row: RowMapping) -> ResourceIndexRecord:
    data = dict(row)
    descriptor_fields = {key: data[key] for key in ResourceDescriptor.model_fields if key in data}
    return ResourceIndexRecord(
        resource_index_id=data["resource_index_id"],
        descriptor=ResourceDescriptor(**descriptor_fields),
        created_at=data.get("created_at"),
    )


def _row_to_validation_run(row: RowMapping) -> ReferenceValidationRun:
    data = dict(row)
    data["broken_references"] = [
        BrokenReference(**item) for item in data.get("broken_references", [])
    ]
    data["orphaned_resources"] = [
        OrphanedResource(**item) for item in data.get("orphaned_resources", [])
    ]
    return ReferenceValidationRun(**data)


def _filter_scope(
    records: list[ResourceIndexRecord],
    scope: list[str] | None,
) -> list[ResourceIndexRecord]:
    if not scope:
        return records
    requested = set(scope)
    return [record for record in records if requested.intersection(record.descriptor.owner_scope)]


__all__ = [
    "ResourceRegistryRepository",
    "aion_broken_reference_records",
    "aion_orphaned_resource_records",
    "aion_reference_validation_runs",
    "aion_registry_backlinks",
    "aion_registry_rebuild_runs",
    "aion_registry_snapshots",
    "aion_resource_index_records",
    "aion_resource_reference_links",
    "registry_metadata",
]
