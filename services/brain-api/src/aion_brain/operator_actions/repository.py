"""Persistence for governed operator action records."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import (
    Boolean,
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
from sqlalchemy.engine import Engine
from sqlalchemy.pool import QueuePool, StaticPool
from sqlalchemy.types import JSON

from aion_brain.contracts.operator_actions import (
    OperatorActionBlocker,
    OperatorActionPreview,
    OperatorActionQuery,
    OperatorActionQueryResult,
    OperatorActionRequest,
    OperatorActionReview,
)

operator_action_metadata = MetaData()
json_payload_type = JSON().with_variant(JSONB(), "postgresql")

aion_operator_action_requests = Table(
    "aion_operator_action_requests",
    operator_action_metadata,
    Column("operator_action_request_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("actor_id", Text, nullable=True),
    Column("workspace_id", Text, nullable=True),
    Column("action_key", Text, nullable=False),
    Column("action_type", Text, nullable=False),
    Column("target_type", Text, nullable=False),
    Column("target_id", Text, nullable=True),
    Column("status", Text, nullable=False),
    Column("mode", Text, nullable=False),
    Column("risk_level", Text, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("request_payload_hash", Text, nullable=False),
    Column("redacted_request_payload", json_payload_type, nullable=False),
    Column("required_policy_actions", json_payload_type, nullable=False),
    Column("required_approvals", json_payload_type, nullable=False),
    Column("required_evidence_refs", json_payload_type, nullable=False),
    Column("blocker_refs", json_payload_type, nullable=False),
    Column("preview_id", Text, nullable=True),
    Column("review_id", Text, nullable=True),
    Column("execution_allowed", Boolean, nullable=False),
    Column("external_calls_allowed", Boolean, nullable=False),
    Column("activation_allowed", Boolean, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("reviewed_at", DateTime(timezone=True), nullable=True),
    Column("archived_at", DateTime(timezone=True), nullable=True),
    Column("deleted_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_operator_action_requests_trace_id", "trace_id"),
    Index("ix_aion_operator_action_requests_actor_id", "actor_id"),
    Index("ix_aion_operator_action_requests_workspace_id", "workspace_id"),
    Index("ix_aion_operator_action_requests_action_key", "action_key"),
    Index("ix_aion_operator_action_requests_action_type", "action_type"),
    Index("ix_aion_operator_action_requests_target_type", "target_type"),
    Index("ix_aion_operator_action_requests_status", "status"),
    Index("ix_aion_operator_action_requests_mode", "mode"),
    Index("ix_aion_operator_action_requests_risk_level", "risk_level"),
    Index("ix_aion_operator_action_requests_execution_allowed", "execution_allowed"),
    Index("ix_aion_operator_action_requests_external_calls_allowed", "external_calls_allowed"),
    Index("ix_aion_operator_action_requests_activation_allowed", "activation_allowed"),
    Index("ix_aion_operator_action_requests_created_at", "created_at"),
    Index("ix_aion_operator_action_requests_deleted_at", "deleted_at"),
)

aion_operator_action_previews = Table(
    "aion_operator_action_previews",
    operator_action_metadata,
    Column("operator_action_preview_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("operator_action_request_id", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("preview_type", Text, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("expected_effects", json_payload_type, nullable=False),
    Column("blocked_effects", json_payload_type, nullable=False),
    Column("dry_run_result", json_payload_type, nullable=False),
    Column("would_execute", Boolean, nullable=False),
    Column("execution_allowed", Boolean, nullable=False),
    Column("external_calls_allowed", Boolean, nullable=False),
    Column("activation_allowed", Boolean, nullable=False),
    Column("blockers", json_payload_type, nullable=False),
    Column("warnings", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Index("ix_aion_operator_action_previews_trace_id", "trace_id"),
    Index("ix_aion_operator_action_previews_request_id", "operator_action_request_id"),
    Index("ix_aion_operator_action_previews_status", "status"),
    Index("ix_aion_operator_action_previews_preview_type", "preview_type"),
    Index("ix_aion_operator_action_previews_would_execute", "would_execute"),
    Index("ix_aion_operator_action_previews_execution_allowed", "execution_allowed"),
    Index("ix_aion_operator_action_previews_external_calls_allowed", "external_calls_allowed"),
    Index("ix_aion_operator_action_previews_activation_allowed", "activation_allowed"),
    Index("ix_aion_operator_action_previews_created_at", "created_at"),
)

aion_operator_action_blockers = Table(
    "aion_operator_action_blockers",
    operator_action_metadata,
    Column("operator_action_blocker_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("operator_action_request_id", Text, nullable=True),
    Column("blocker_type", Text, nullable=False),
    Column("severity", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("reason", Text, nullable=False),
    Column("recommended_action", Text, nullable=False),
    Column("source_type", Text, nullable=True),
    Column("source_id", Text, nullable=True),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("resolved_at", DateTime(timezone=True), nullable=True),
    Column("dismissed_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_operator_action_blockers_trace_id", "trace_id"),
    Index("ix_aion_operator_action_blockers_request_id", "operator_action_request_id"),
    Index("ix_aion_operator_action_blockers_blocker_type", "blocker_type"),
    Index("ix_aion_operator_action_blockers_severity", "severity"),
    Index("ix_aion_operator_action_blockers_status", "status"),
    Index("ix_aion_operator_action_blockers_source_type", "source_type"),
    Index("ix_aion_operator_action_blockers_source_id", "source_id"),
    Index("ix_aion_operator_action_blockers_created_at", "created_at"),
)

aion_operator_action_reviews = Table(
    "aion_operator_action_reviews",
    operator_action_metadata,
    Column("operator_action_review_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("operator_action_request_id", Text, nullable=False),
    Column("actor_id", Text, nullable=True),
    Column("workspace_id", Text, nullable=True),
    Column("reviewer_id", Text, nullable=True),
    Column("status", Text, nullable=False),
    Column("decision", Text, nullable=False),
    Column("reason", Text, nullable=False),
    Column("approval_present", Boolean, nullable=False),
    Column("execution_allowed", Boolean, nullable=False),
    Column("blocker_refs", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Index("ix_aion_operator_action_reviews_trace_id", "trace_id"),
    Index("ix_aion_operator_action_reviews_request_id", "operator_action_request_id"),
    Index("ix_aion_operator_action_reviews_actor_id", "actor_id"),
    Index("ix_aion_operator_action_reviews_workspace_id", "workspace_id"),
    Index("ix_aion_operator_action_reviews_reviewer_id", "reviewer_id"),
    Index("ix_aion_operator_action_reviews_status", "status"),
    Index("ix_aion_operator_action_reviews_decision", "decision"),
    Index("ix_aion_operator_action_reviews_execution_allowed", "execution_allowed"),
    Index("ix_aion_operator_action_reviews_created_at", "created_at"),
)


class OperatorActionRepository:
    """Repository for governed operator action records."""

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
            self._engine = _create_engine(database_url)
        else:
            self._engine = engine
        self._auto_create = auto_create
        self._schema_ready = False

    def save_request(self, request: OperatorActionRequest) -> OperatorActionRequest:
        self._ensure_schema()
        now = datetime.now(UTC)
        stored = request.model_copy(update={"created_at": request.created_at or now})
        self._upsert(
            aion_operator_action_requests,
            "operator_action_request_id",
            stored.operator_action_request_id,
            stored.model_dump(mode="python"),
        )
        return stored

    def get_request(self, operator_action_request_id: str) -> OperatorActionRequest | None:
        self._ensure_schema()
        with self._engine.connect() as connection:
            row = (
                connection.execute(
                    select(aion_operator_action_requests).where(
                        aion_operator_action_requests.c.operator_action_request_id
                        == operator_action_request_id
                    )
                )
                .mappings()
                .first()
            )
        return OperatorActionRequest(**dict(row)) if row is not None else None

    def list_requests(
        self,
        query: OperatorActionQuery | None = None,
        *,
        scope: list[str] | None = None,
        status: str | None = None,
        action_type: str | None = None,
        target_type: str | None = None,
        risk_level: str | None = None,
        limit: int = 100,
    ) -> list[OperatorActionRequest]:
        self._ensure_schema()
        if query is not None:
            scope = query.scope
            status = query.status
            action_type = query.action_type
            target_type = query.target_type
            risk_level = query.risk_level
            limit = query.limit
        statement = select(aion_operator_action_requests).where(
            aion_operator_action_requests.c.deleted_at.is_(None)
        )
        if status is not None:
            statement = statement.where(aion_operator_action_requests.c.status == status)
        if action_type is not None:
            statement = statement.where(aion_operator_action_requests.c.action_type == action_type)
        if target_type is not None:
            statement = statement.where(aion_operator_action_requests.c.target_type == target_type)
        if risk_level is not None:
            statement = statement.where(aion_operator_action_requests.c.risk_level == risk_level)
        statement = statement.order_by(aion_operator_action_requests.c.created_at.desc()).limit(
            limit
        )
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
        return [
            OperatorActionRequest(**dict(row))
            for row in rows
            if scope is None or _scope_matches(row["owner_scope"], scope)
        ]

    def save_preview(self, preview: OperatorActionPreview) -> OperatorActionPreview:
        self._ensure_schema()
        stored = preview.model_copy(update={"created_at": preview.created_at or datetime.now(UTC)})
        self._upsert(
            aion_operator_action_previews,
            "operator_action_preview_id",
            stored.operator_action_preview_id,
            stored.model_dump(mode="python"),
        )
        return stored

    def get_preview(self, operator_action_preview_id: str) -> OperatorActionPreview | None:
        self._ensure_schema()
        with self._engine.connect() as connection:
            row = (
                connection.execute(
                    select(aion_operator_action_previews).where(
                        aion_operator_action_previews.c.operator_action_preview_id
                        == operator_action_preview_id
                    )
                )
                .mappings()
                .first()
            )
        return OperatorActionPreview(**dict(row)) if row is not None else None

    def list_previews(
        self,
        *,
        scope: list[str],
        status: str | None = None,
        limit: int = 100,
    ) -> list[OperatorActionPreview]:
        self._ensure_schema()
        statement = select(aion_operator_action_previews)
        if status is not None:
            statement = statement.where(aion_operator_action_previews.c.status == status)
        statement = statement.order_by(aion_operator_action_previews.c.created_at.desc()).limit(
            limit
        )
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
        return [
            OperatorActionPreview(**dict(row))
            for row in rows
            if _scope_matches(row["owner_scope"], scope)
        ]

    def save_blocker(self, blocker: OperatorActionBlocker) -> OperatorActionBlocker:
        self._ensure_schema()
        stored = blocker.model_copy(update={"created_at": blocker.created_at or datetime.now(UTC)})
        self._upsert(
            aion_operator_action_blockers,
            "operator_action_blocker_id",
            stored.operator_action_blocker_id,
            stored.model_dump(mode="python"),
        )
        return stored

    def get_blocker(self, operator_action_blocker_id: str) -> OperatorActionBlocker | None:
        self._ensure_schema()
        with self._engine.connect() as connection:
            row = (
                connection.execute(
                    select(aion_operator_action_blockers).where(
                        aion_operator_action_blockers.c.operator_action_blocker_id
                        == operator_action_blocker_id
                    )
                )
                .mappings()
                .first()
            )
        return OperatorActionBlocker(**dict(row)) if row is not None else None

    def list_blockers(
        self,
        *,
        scope: list[str] | None = None,
        operator_action_request_id: str | None = None,
        status: str | None = None,
        severity: str | None = None,
        limit: int = 100,
    ) -> list[OperatorActionBlocker]:
        self._ensure_schema()
        statement = select(aion_operator_action_blockers)
        if operator_action_request_id is not None:
            statement = statement.where(
                aion_operator_action_blockers.c.operator_action_request_id
                == operator_action_request_id
            )
        if status is not None:
            statement = statement.where(aion_operator_action_blockers.c.status == status)
        if severity is not None:
            statement = statement.where(aion_operator_action_blockers.c.severity == severity)
        statement = statement.order_by(aion_operator_action_blockers.c.created_at.desc()).limit(
            limit
        )
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
        blockers = [OperatorActionBlocker(**dict(row)) for row in rows]
        if scope is None:
            return blockers
        request_ids = {
            blocker.operator_action_request_id
            for blocker in blockers
            if blocker.operator_action_request_id is not None
        }
        request_scopes = {
            request_id: request.owner_scope
            for request_id in request_ids
            if (request := self.get_request(request_id)) is not None
        }
        return [
            blocker
            for blocker in blockers
            if blocker.operator_action_request_id is None
            or _scope_matches(request_scopes.get(blocker.operator_action_request_id), scope)
        ]

    def save_review(self, review: OperatorActionReview) -> OperatorActionReview:
        self._ensure_schema()
        stored = review.model_copy(update={"created_at": review.created_at or datetime.now(UTC)})
        self._upsert(
            aion_operator_action_reviews,
            "operator_action_review_id",
            stored.operator_action_review_id,
            stored.model_dump(mode="python"),
        )
        return stored

    def list_reviews(
        self,
        *,
        scope: list[str],
        operator_action_request_id: str | None = None,
        decision: str | None = None,
        limit: int = 100,
    ) -> list[OperatorActionReview]:
        self._ensure_schema()
        statement = select(aion_operator_action_reviews)
        if operator_action_request_id is not None:
            statement = statement.where(
                aion_operator_action_reviews.c.operator_action_request_id
                == operator_action_request_id
            )
        if decision is not None:
            statement = statement.where(aion_operator_action_reviews.c.decision == decision)
        statement = statement.order_by(aion_operator_action_reviews.c.created_at.desc()).limit(
            limit
        )
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
        reviews = [OperatorActionReview(**dict(row)) for row in rows]
        request_ids = {review.operator_action_request_id for review in reviews}
        request_scopes = {
            request_id: request.owner_scope
            for request_id in request_ids
            if (request := self.get_request(request_id)) is not None
        }
        return [
            review
            for review in reviews
            if _scope_matches(request_scopes.get(review.operator_action_request_id), scope)
        ]

    def query(self, query: OperatorActionQuery) -> OperatorActionQueryResult:
        requests = self.list_requests(query)
        request_ids = {request.operator_action_request_id for request in requests}
        previews = [
            preview
            for preview in self.list_previews(scope=query.scope, limit=query.limit)
            if preview.operator_action_request_id in request_ids
        ]
        blockers = [
            blocker
            for blocker in self.list_blockers(scope=query.scope, limit=query.limit)
            if blocker.operator_action_request_id in request_ids
        ]
        reviews = [
            review
            for review in self.list_reviews(scope=query.scope, limit=query.limit)
            if review.operator_action_request_id in request_ids
        ]
        return OperatorActionQueryResult(
            requests=requests,
            previews=previews,
            blockers=blockers,
            reviews=reviews,
            total_count=len(requests),
            constraints=[
                "operator_actions_are_dry_run_only",
                "operator_action_reviews_do_not_execute",
            ],
            metadata={"source": "operator_action_repository"},
        )

    def _upsert(self, table: Table, key: str, value: str, payload: dict[str, Any]) -> None:
        with self._engine.begin() as connection:
            existing = connection.execute(select(table.c[key]).where(table.c[key] == value)).first()
            if existing is None:
                connection.execute(insert(table).values(**payload))
            else:
                connection.execute(update(table).where(table.c[key] == value).values(**payload))

    def _ensure_schema(self) -> None:
        if self._schema_ready:
            return
        if self._auto_create:
            operator_action_metadata.create_all(self._engine)
        self._schema_ready = True


def _create_engine(database_url: str) -> Engine:
    if database_url.startswith("sqlite"):
        return create_engine(
            database_url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
    return create_engine(database_url, poolclass=QueuePool, pool_pre_ping=True)


def _scope_matches(owner_scope: object, query_scope: list[str]) -> bool:
    if owner_scope is None:
        return True
    if not isinstance(owner_scope, list):
        return True
    return bool(set(str(item) for item in owner_scope).intersection(query_scope))


__all__ = [
    "OperatorActionRepository",
    "aion_operator_action_blockers",
    "aion_operator_action_previews",
    "aion_operator_action_requests",
    "aion_operator_action_reviews",
    "operator_action_metadata",
]
