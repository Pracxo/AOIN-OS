"""Persistence for the AION entity resolver and canonical reference layer."""

from __future__ import annotations

from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
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

from aion_brain.contracts.entities import (
    EntityAlias,
    EntityMention,
    EntityMergeProposal,
    EntityQuery,
    EntityQueryResult,
    EntityRecord,
    EntityResolutionResult,
    EntitySplitProposal,
    ReferenceLink,
)

entity_metadata = MetaData()
json_payload_type = JSON().with_variant(JSONB(), "postgresql")

aion_entities = Table(
    "aion_entities",
    entity_metadata,
    Column("entity_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("canonical_name", Text, nullable=False),
    Column("normalized_name", Text, nullable=False),
    Column("entity_type", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("concept_refs", json_payload_type, nullable=False),
    Column("evidence_refs", json_payload_type, nullable=False),
    Column("memory_refs", json_payload_type, nullable=False),
    Column("belief_refs", json_payload_type, nullable=False),
    Column("graph_refs", json_payload_type, nullable=False),
    Column("confidence", Float, nullable=False),
    Column("sensitivity", Text, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=True),
    Column("updated_at", DateTime(timezone=True), nullable=True),
    Column("merged_into_entity_id", Text, nullable=True),
    Column("archived_at", DateTime(timezone=True), nullable=True),
    Column("deleted_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_entities_normalized_name", "normalized_name"),
    Index("ix_aion_entities_entity_type", "entity_type"),
    Index("ix_aion_entities_status", "status"),
    Index("ix_aion_entities_confidence", "confidence"),
    Index("ix_aion_entities_created_at", "created_at"),
    Index("ix_aion_entities_deleted_at", "deleted_at"),
)

aion_entity_aliases = Table(
    "aion_entity_aliases",
    entity_metadata,
    Column("alias_id", Text, primary_key=True),
    Column("entity_id", Text, nullable=False),
    Column("alias", Text, nullable=False),
    Column("normalized_alias", Text, nullable=False),
    Column("alias_type", Text, nullable=False),
    Column("confidence", Float, nullable=False),
    Column("source_type", Text, nullable=True),
    Column("source_id", Text, nullable=True),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=True),
    Column("deleted_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_entity_aliases_entity_id", "entity_id"),
    Index("ix_aion_entity_aliases_normalized_alias", "normalized_alias"),
    Index("ix_aion_entity_aliases_alias_type", "alias_type"),
    Index("ix_aion_entity_aliases_deleted_at", "deleted_at"),
)

aion_entity_mentions = Table(
    "aion_entity_mentions",
    entity_metadata,
    Column("mention_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("entity_id", Text, nullable=True),
    Column("source_type", Text, nullable=False),
    Column("source_id", Text, nullable=False),
    Column("mention_text", Text, nullable=False),
    Column("normalized_mention", Text, nullable=False),
    Column("mention_type", Text, nullable=False),
    Column("start_char", Integer, nullable=True),
    Column("end_char", Integer, nullable=True),
    Column("confidence", Float, nullable=False),
    Column("resolved", Boolean, nullable=False),
    Column("resolution_score", Float, nullable=True),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=True),
    Column("deleted_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_entity_mentions_entity_id", "entity_id"),
    Index("ix_aion_entity_mentions_trace_id", "trace_id"),
    Index("ix_aion_entity_mentions_source_type", "source_type"),
    Index("ix_aion_entity_mentions_source_id", "source_id"),
    Index("ix_aion_entity_mentions_normalized_mention", "normalized_mention"),
    Index("ix_aion_entity_mentions_resolved", "resolved"),
    Index("ix_aion_entity_mentions_deleted_at", "deleted_at"),
)

aion_reference_links = Table(
    "aion_reference_links",
    entity_metadata,
    Column("reference_link_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("source_type", Text, nullable=False),
    Column("source_id", Text, nullable=False),
    Column("target_type", Text, nullable=False),
    Column("target_id", Text, nullable=False),
    Column("relation_type", Text, nullable=False),
    Column("entity_id", Text, nullable=True),
    Column("concept_id", Text, nullable=True),
    Column("confidence", Float, nullable=False),
    Column("evidence_refs", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=True),
    Column("deleted_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_reference_links_trace_id", "trace_id"),
    Index("ix_aion_reference_links_source", "source_type", "source_id"),
    Index("ix_aion_reference_links_target", "target_type", "target_id"),
    Index("ix_aion_reference_links_entity_id", "entity_id"),
    Index("ix_aion_reference_links_concept_id", "concept_id"),
    Index("ix_aion_reference_links_relation_type", "relation_type"),
    Index("ix_aion_reference_links_deleted_at", "deleted_at"),
)

aion_entity_resolution_runs = Table(
    "aion_entity_resolution_runs",
    entity_metadata,
    Column("resolution_run_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("status", Text, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("source_type", Text, nullable=True),
    Column("source_id", Text, nullable=True),
    Column("result", json_payload_type, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=True),
    Column("completed_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_entity_resolution_runs_trace_id", "trace_id"),
    Index("ix_aion_entity_resolution_runs_status", "status"),
    Index("ix_aion_entity_resolution_runs_source", "source_type", "source_id"),
)

aion_entity_merge_proposals = Table(
    "aion_entity_merge_proposals",
    entity_metadata,
    Column("merge_proposal_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("primary_entity_id", Text, nullable=False),
    Column("duplicate_entity_id", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("score", Float, nullable=False),
    Column("reason", Text, nullable=False),
    Column("evidence_refs", json_payload_type, nullable=False),
    Column("approval_request_id", Text, nullable=True),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=True),
    Column("resolved_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_entity_merge_proposals_status", "status"),
    Index("ix_aion_entity_merge_proposals_primary", "primary_entity_id"),
    Index("ix_aion_entity_merge_proposals_duplicate", "duplicate_entity_id"),
)

aion_entity_split_proposals = Table(
    "aion_entity_split_proposals",
    entity_metadata,
    Column("split_proposal_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("entity_id", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("reason", Text, nullable=False),
    Column("proposed_entities", json_payload_type, nullable=False),
    Column("evidence_refs", json_payload_type, nullable=False),
    Column("approval_request_id", Text, nullable=True),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=True),
    Column("resolved_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_entity_split_proposals_status", "status"),
    Index("ix_aion_entity_split_proposals_entity_id", "entity_id"),
)


class EntityRepository:
    """Repository for canonical entities, aliases, mentions, and references."""

    def __init__(
        self,
        database_url: str | None = None,
        *,
        engine: Engine | None = None,
        auto_create: bool = True,
    ) -> None:
        url = database_url or "sqlite+pysqlite:///:memory:"
        self._engine = engine or create_engine(
            url,
            connect_args={"check_same_thread": False} if url.startswith("sqlite") else {},
            poolclass=StaticPool if url.startswith("sqlite") else QueuePool,
            pool_pre_ping=not url.startswith("sqlite"),
        )
        self._auto_create = auto_create
        self._schema_ready = False

    def save_entity(self, entity: EntityRecord) -> EntityRecord:
        values = entity.model_dump(mode="python")
        self._upsert(aion_entities, "entity_id", entity.entity_id, values)
        return entity

    def get_entity(self, entity_id: str) -> EntityRecord | None:
        self._ensure_schema()
        row = self._first(select(aion_entities).where(aion_entities.c.entity_id == entity_id))
        return _row_to_entity(row) if row is not None else None

    def find_entity_by_normalized_name(
        self,
        normalized_name: str,
        scope: list[str],
    ) -> EntityRecord | None:
        self._ensure_schema()
        rows = self._all(
            select(aion_entities).where(
                aion_entities.c.normalized_name == normalized_name,
                aion_entities.c.deleted_at.is_(None),
            )
        )
        for row in rows:
            entity = _row_to_entity(row)
            if entity.status in {"active", "proposed"} and _scope_matches(
                entity.owner_scope,
                scope,
            ):
                return entity
        return None

    def query_entities(self, query: EntityQuery) -> EntityQueryResult:
        self._ensure_schema()
        rows = self._all(select(aion_entities).order_by(aion_entities.c.created_at.desc()))
        normalized_query = query.query.lower() if query.query else None
        entities: list[EntityRecord] = []
        for row in rows:
            entity = _row_to_entity(row)
            if entity.deleted_at is not None and not query.include_deleted:
                continue
            if entity.status == "merged" and not query.include_merged:
                continue
            if query.statuses and entity.status not in query.statuses:
                continue
            if query.entity_types and entity.entity_type not in query.entity_types:
                continue
            if query.min_confidence is not None and entity.confidence < query.min_confidence:
                continue
            if not _scope_matches(entity.owner_scope, query.scope):
                continue
            if query.concept_refs and not _intersects(entity.concept_refs, query.concept_refs):
                continue
            if query.evidence_refs and not _intersects(entity.evidence_refs, query.evidence_refs):
                continue
            if query.memory_refs and not _intersects(entity.memory_refs, query.memory_refs):
                continue
            if query.belief_refs and not _intersects(entity.belief_refs, query.belief_refs):
                continue
            if normalized_query and not self._entity_matches_query(entity, normalized_query):
                continue
            entities.append(entity)
            if len(entities) >= query.limit:
                break
        entity_ids = [entity.entity_id for entity in entities]
        return EntityQueryResult(
            entities=entities,
            aliases=self.list_aliases(entity_ids=entity_ids) if entity_ids else [],
            mentions=self.list_mentions(
                scope=query.scope,
                entity_ids=entity_ids,
                limit=query.limit,
            ),
            total_count=len(entities),
            constraints=[],
            metadata={},
        )

    def save_alias(self, alias: EntityAlias) -> EntityAlias:
        values = alias.model_dump(mode="python")
        self._upsert(aion_entity_aliases, "alias_id", alias.alias_id, values)
        return alias

    def get_alias(self, alias_id: str) -> EntityAlias | None:
        self._ensure_schema()
        row = self._first(
            select(aion_entity_aliases).where(aion_entity_aliases.c.alias_id == alias_id)
        )
        return _row_to_alias(row) if row is not None else None

    def list_aliases(
        self,
        *,
        entity_ids: list[str] | None = None,
        normalized_alias: str | None = None,
        include_deleted: bool = False,
    ) -> list[EntityAlias]:
        self._ensure_schema()
        statement = select(aion_entity_aliases)
        if entity_ids:
            statement = statement.where(aion_entity_aliases.c.entity_id.in_(entity_ids))
        if normalized_alias:
            statement = statement.where(aion_entity_aliases.c.normalized_alias == normalized_alias)
        if not include_deleted:
            statement = statement.where(aion_entity_aliases.c.deleted_at.is_(None))
        return [_row_to_alias(row) for row in self._all(statement)]

    def save_mention(self, mention: EntityMention) -> EntityMention:
        values = mention.model_dump(mode="python")
        self._upsert(aion_entity_mentions, "mention_id", mention.mention_id, values)
        return mention

    def get_mention(self, mention_id: str) -> EntityMention | None:
        self._ensure_schema()
        row = self._first(
            select(aion_entity_mentions).where(aion_entity_mentions.c.mention_id == mention_id)
        )
        return _row_to_mention(row) if row is not None else None

    def list_mentions(
        self,
        *,
        scope: list[str],
        entity_ids: list[str] | None = None,
        source_type: str | None = None,
        source_id: str | None = None,
        resolved: bool | None = None,
        min_confidence: float | None = None,
        include_deleted: bool = False,
        limit: int = 100,
    ) -> list[EntityMention]:
        self._ensure_schema()
        statement = select(aion_entity_mentions).order_by(aion_entity_mentions.c.created_at.desc())
        if entity_ids:
            statement = statement.where(aion_entity_mentions.c.entity_id.in_(entity_ids))
        if source_type:
            statement = statement.where(aion_entity_mentions.c.source_type == source_type)
        if source_id:
            statement = statement.where(aion_entity_mentions.c.source_id == source_id)
        if resolved is not None:
            statement = statement.where(aion_entity_mentions.c.resolved == resolved)
        if not include_deleted:
            statement = statement.where(aion_entity_mentions.c.deleted_at.is_(None))
        mentions: list[EntityMention] = []
        for row in self._all(statement):
            mention = _row_to_mention(row)
            if min_confidence is not None and mention.confidence < min_confidence:
                continue
            if not _scope_matches(mention.owner_scope, scope):
                continue
            mentions.append(mention)
            if len(mentions) >= limit:
                break
        return mentions

    def save_reference_link(self, link: ReferenceLink) -> ReferenceLink:
        values = link.model_dump(mode="python")
        self._upsert(aion_reference_links, "reference_link_id", link.reference_link_id, values)
        return link

    def get_reference_link(self, reference_link_id: str) -> ReferenceLink | None:
        self._ensure_schema()
        row = self._first(
            select(aion_reference_links).where(
                aion_reference_links.c.reference_link_id == reference_link_id
            )
        )
        return _row_to_link(row) if row is not None else None

    def list_reference_links(
        self,
        *,
        entity_id: str | None = None,
        concept_id: str | None = None,
        source_type: str | None = None,
        source_id: str | None = None,
        target_type: str | None = None,
        target_id: str | None = None,
        include_deleted: bool = False,
        limit: int = 100,
    ) -> list[ReferenceLink]:
        self._ensure_schema()
        statement = select(aion_reference_links).order_by(aion_reference_links.c.created_at.desc())
        if entity_id:
            statement = statement.where(aion_reference_links.c.entity_id == entity_id)
        if concept_id:
            statement = statement.where(aion_reference_links.c.concept_id == concept_id)
        if source_type:
            statement = statement.where(aion_reference_links.c.source_type == source_type)
        if source_id:
            statement = statement.where(aion_reference_links.c.source_id == source_id)
        if target_type:
            statement = statement.where(aion_reference_links.c.target_type == target_type)
        if target_id:
            statement = statement.where(aion_reference_links.c.target_id == target_id)
        if not include_deleted:
            statement = statement.where(aion_reference_links.c.deleted_at.is_(None))
        return [_row_to_link(row) for row in self._all(statement)[:limit]]

    def save_resolution_result(self, result: EntityResolutionResult) -> EntityResolutionResult:
        values = {
            "resolution_run_id": result.resolution_run_id,
            "trace_id": result.created_mentions[0].trace_id if result.created_mentions else None,
            "status": result.status,
            "owner_scope": result.owner_scope,
            "source_type": result.source_type,
            "source_id": result.source_id,
            "result": result.model_dump(mode="json"),
            "created_at": result.created_at,
            "completed_at": result.completed_at,
        }
        self._upsert(
            aion_entity_resolution_runs,
            "resolution_run_id",
            result.resolution_run_id,
            values,
        )
        return result

    def get_resolution_result(self, resolution_run_id: str) -> EntityResolutionResult | None:
        self._ensure_schema()
        row = self._first(
            select(aion_entity_resolution_runs).where(
                aion_entity_resolution_runs.c.resolution_run_id == resolution_run_id
            )
        )
        if row is None:
            return None
        payload = row["result"]
        if isinstance(payload, dict):
            return EntityResolutionResult(**payload)
        return None

    def save_merge_proposal(self, proposal: EntityMergeProposal) -> EntityMergeProposal:
        values = proposal.model_dump(mode="python")
        self._upsert(
            aion_entity_merge_proposals,
            "merge_proposal_id",
            proposal.merge_proposal_id,
            values,
        )
        return proposal

    def get_merge_proposal(self, proposal_id: str) -> EntityMergeProposal | None:
        self._ensure_schema()
        row = self._first(
            select(aion_entity_merge_proposals).where(
                aion_entity_merge_proposals.c.merge_proposal_id == proposal_id
            )
        )
        return _row_to_merge(row) if row is not None else None

    def list_merge_proposals(
        self,
        *,
        status: str | None = None,
        limit: int = 100,
    ) -> list[EntityMergeProposal]:
        self._ensure_schema()
        statement = select(aion_entity_merge_proposals).order_by(
            aion_entity_merge_proposals.c.created_at.desc()
        )
        if status:
            statement = statement.where(aion_entity_merge_proposals.c.status == status)
        return [_row_to_merge(row) for row in self._all(statement)[:limit]]

    def save_split_proposal(self, proposal: EntitySplitProposal) -> EntitySplitProposal:
        values = proposal.model_dump(mode="python")
        self._upsert(
            aion_entity_split_proposals,
            "split_proposal_id",
            proposal.split_proposal_id,
            values,
        )
        return proposal

    def get_split_proposal(self, proposal_id: str) -> EntitySplitProposal | None:
        self._ensure_schema()
        row = self._first(
            select(aion_entity_split_proposals).where(
                aion_entity_split_proposals.c.split_proposal_id == proposal_id
            )
        )
        return _row_to_split(row) if row is not None else None

    def list_split_proposals(
        self,
        *,
        status: str | None = None,
        limit: int = 100,
    ) -> list[EntitySplitProposal]:
        self._ensure_schema()
        statement = select(aion_entity_split_proposals).order_by(
            aion_entity_split_proposals.c.created_at.desc()
        )
        if status:
            statement = statement.where(aion_entity_split_proposals.c.status == status)
        return [_row_to_split(row) for row in self._all(statement)[:limit]]

    def _entity_matches_query(self, entity: EntityRecord, normalized_query: str) -> bool:
        if (
            normalized_query in entity.normalized_name
            or normalized_query in entity.canonical_name.lower()
        ):
            return True
        aliases = self.list_aliases(entity_ids=[entity.entity_id])
        return any(normalized_query in alias.normalized_alias for alias in aliases)

    def _upsert(
        self,
        table: Table,
        key_column: str,
        key_value: str,
        values: dict[str, Any],
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

    def _ensure_schema(self) -> None:
        if self._schema_ready:
            return
        if self._auto_create:
            entity_metadata.create_all(self._engine)
        self._schema_ready = True

    def _first(self, statement: Any) -> RowMapping | None:
        with self._engine.begin() as connection:
            row = connection.execute(statement).mappings().first()
        return row

    def _all(self, statement: Any) -> list[RowMapping]:
        with self._engine.begin() as connection:
            rows = list(connection.execute(statement).mappings().all())
        return rows


def _row_to_entity(row: RowMapping) -> EntityRecord:
    return EntityRecord(**dict(row))


def _row_to_alias(row: RowMapping) -> EntityAlias:
    return EntityAlias(**dict(row))


def _row_to_mention(row: RowMapping) -> EntityMention:
    data = dict(row)
    return EntityMention(**data)


def _row_to_link(row: RowMapping) -> ReferenceLink:
    return ReferenceLink(**dict(row))


def _row_to_merge(row: RowMapping) -> EntityMergeProposal:
    return EntityMergeProposal(**dict(row))


def _row_to_split(row: RowMapping) -> EntitySplitProposal:
    return EntitySplitProposal(**dict(row))


def _scope_matches(owner_scope: list[str], requested_scope: list[str]) -> bool:
    return bool(set(owner_scope).intersection(set(requested_scope)))


def _intersects(left: list[str], right: list[str]) -> bool:
    return bool(set(left).intersection(set(right)))
