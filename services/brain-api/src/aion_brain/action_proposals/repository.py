"""Persistent repository for action proposal broker records."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
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

from aion_brain.contracts.action_proposals import (
    ActionBlocker,
    ActionProposal,
    ActionProposalQuery,
    ActionProposalQueryResult,
    ActionProposalReview,
    ToolIntentReview,
)
from aion_brain.contracts.execution_handoffs import ExecutionHandoff

action_proposal_metadata = MetaData()
json_payload_type = JSON().with_variant(JSONB(), "postgresql")

aion_action_proposals = Table(
    "aion_action_proposals",
    action_proposal_metadata,
    Column("action_proposal_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("actor_id", Text, nullable=True),
    Column("workspace_id", Text, nullable=True),
    Column("source_type", Text, nullable=False),
    Column("source_id", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("proposal_type", Text, nullable=False),
    Column("title", Text, nullable=False),
    Column("description", Text, nullable=False),
    Column("action_type", Text, nullable=False),
    Column("target_type", Text, nullable=False),
    Column("target_id", Text, nullable=True),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("proposed_payload", json_payload_type, nullable=False),
    Column("required_permissions", json_payload_type, nullable=False),
    Column("required_approvals", json_payload_type, nullable=False),
    Column("risk_level", Text, nullable=False),
    Column("autonomy_mode_required", Text, nullable=True),
    Column("sandbox_profile_id", Text, nullable=True),
    Column("capability_refs", json_payload_type, nullable=False),
    Column("evidence_refs", json_payload_type, nullable=False),
    Column("decision_refs", json_payload_type, nullable=False),
    Column("model_output_refs", json_payload_type, nullable=False),
    Column("tool_intent_refs", json_payload_type, nullable=False),
    Column("blocker_refs", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    Column("reviewed_at", DateTime(timezone=True), nullable=True),
    Column("archived_at", DateTime(timezone=True), nullable=True),
    Column("deleted_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_action_proposals_trace_id", "trace_id"),
    Index("ix_aion_action_proposals_actor_id", "actor_id"),
    Index("ix_aion_action_proposals_workspace_id", "workspace_id"),
    Index("ix_aion_action_proposals_source_type", "source_type"),
    Index("ix_aion_action_proposals_source_id", "source_id"),
    Index("ix_aion_action_proposals_status", "status"),
    Index("ix_aion_action_proposals_proposal_type", "proposal_type"),
    Index("ix_aion_action_proposals_action_type", "action_type"),
    Index("ix_aion_action_proposals_target_type", "target_type"),
    Index("ix_aion_action_proposals_risk_level", "risk_level"),
    Index("ix_aion_action_proposals_created_at", "created_at"),
    Index("ix_aion_action_proposals_deleted_at", "deleted_at"),
)

aion_action_blockers = Table(
    "aion_action_blockers",
    action_proposal_metadata,
    Column("action_blocker_id", Text, primary_key=True),
    Column("action_proposal_id", Text, nullable=True),
    Column("trace_id", Text, nullable=True),
    Column("blocker_type", Text, nullable=False),
    Column("severity", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("reason", Text, nullable=False),
    Column("missing_requirement", Text, nullable=True),
    Column("source_type", Text, nullable=True),
    Column("source_id", Text, nullable=True),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("resolved_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_action_blockers_action_proposal_id", "action_proposal_id"),
    Index("ix_aion_action_blockers_trace_id", "trace_id"),
    Index("ix_aion_action_blockers_blocker_type", "blocker_type"),
    Index("ix_aion_action_blockers_severity", "severity"),
    Index("ix_aion_action_blockers_status", "status"),
    Index("ix_aion_action_blockers_source_type", "source_type"),
    Index("ix_aion_action_blockers_source_id", "source_id"),
    Index("ix_aion_action_blockers_created_at", "created_at"),
)

aion_action_proposal_reviews = Table(
    "aion_action_proposal_reviews",
    action_proposal_metadata,
    Column("action_review_id", Text, primary_key=True),
    Column(
        "action_proposal_id",
        Text,
        ForeignKey("aion_action_proposals.action_proposal_id"),
        nullable=False,
    ),
    Column("trace_id", Text, nullable=True),
    Column("actor_id", Text, nullable=True),
    Column("workspace_id", Text, nullable=True),
    Column("status", Text, nullable=False),
    Column("decision", Text, nullable=False),
    Column("reviewer_id", Text, nullable=True),
    Column("reason", Text, nullable=False),
    Column("policy_decision_id", Text, nullable=True),
    Column("risk_assessment_id", Text, nullable=True),
    Column("autonomy_decision_id", Text, nullable=True),
    Column("approval_request_id", Text, nullable=True),
    Column("blocker_refs", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Index("ix_aion_action_reviews_action_proposal_id", "action_proposal_id"),
    Index("ix_aion_action_reviews_trace_id", "trace_id"),
    Index("ix_aion_action_reviews_actor_id", "actor_id"),
    Index("ix_aion_action_reviews_workspace_id", "workspace_id"),
    Index("ix_aion_action_reviews_status", "status"),
    Index("ix_aion_action_reviews_decision", "decision"),
    Index("ix_aion_action_reviews_reviewer_id", "reviewer_id"),
    Index("ix_aion_action_reviews_created_at", "created_at"),
)

aion_execution_handoffs = Table(
    "aion_execution_handoffs",
    action_proposal_metadata,
    Column("execution_handoff_id", Text, primary_key=True),
    Column(
        "action_proposal_id",
        Text,
        ForeignKey("aion_action_proposals.action_proposal_id"),
        nullable=False,
    ),
    Column("trace_id", Text, nullable=True),
    Column("actor_id", Text, nullable=True),
    Column("workspace_id", Text, nullable=True),
    Column("status", Text, nullable=False),
    Column("handoff_type", Text, nullable=False),
    Column("target_system", Text, nullable=False),
    Column("target_request_id", Text, nullable=True),
    Column("target_run_id", Text, nullable=True),
    Column("handoff_payload", json_payload_type, nullable=False),
    Column("policy_decision_id", Text, nullable=True),
    Column("risk_assessment_id", Text, nullable=True),
    Column("autonomy_decision_id", Text, nullable=True),
    Column("approval_request_id", Text, nullable=True),
    Column("blocker_refs", json_payload_type, nullable=False),
    Column("result", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("completed_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_execution_handoffs_action_proposal_id", "action_proposal_id"),
    Index("ix_aion_execution_handoffs_trace_id", "trace_id"),
    Index("ix_aion_execution_handoffs_actor_id", "actor_id"),
    Index("ix_aion_execution_handoffs_workspace_id", "workspace_id"),
    Index("ix_aion_execution_handoffs_status", "status"),
    Index("ix_aion_execution_handoffs_handoff_type", "handoff_type"),
    Index("ix_aion_execution_handoffs_target_system", "target_system"),
    Index("ix_aion_execution_handoffs_target_request_id", "target_request_id"),
    Index("ix_aion_execution_handoffs_target_run_id", "target_run_id"),
    Index("ix_aion_execution_handoffs_created_at", "created_at"),
)

aion_tool_intent_reviews = Table(
    "aion_tool_intent_reviews",
    action_proposal_metadata,
    Column("tool_intent_review_id", Text, primary_key=True),
    Column("tool_intent_id", Text, nullable=False),
    Column("trace_id", Text, nullable=True),
    Column("status", Text, nullable=False),
    Column("decision", Text, nullable=False),
    Column("action_proposal_id", Text, nullable=True),
    Column("blocker_refs", json_payload_type, nullable=False),
    Column("reason", Text, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Index("ix_aion_tool_intent_reviews_tool_intent_id", "tool_intent_id"),
    Index("ix_aion_tool_intent_reviews_trace_id", "trace_id"),
    Index("ix_aion_tool_intent_reviews_status", "status"),
    Index("ix_aion_tool_intent_reviews_decision", "decision"),
    Index("ix_aion_tool_intent_reviews_action_proposal_id", "action_proposal_id"),
    Index("ix_aion_tool_intent_reviews_created_at", "created_at"),
)


class ActionProposalRepository:
    """Repository for action proposal broker contracts."""

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
                    database_url, connect_args={"check_same_thread": False}, poolclass=StaticPool
                )
            else:
                self._engine = create_engine(database_url, poolclass=QueuePool, pool_pre_ping=True)
        else:
            self._engine = engine
        self._auto_create = auto_create
        self._schema_ready = False

    def save_proposal(self, proposal: ActionProposal) -> ActionProposal:
        self._ensure_schema()
        now = datetime.now(UTC)
        stored = proposal.model_copy(
            update={
                "created_at": proposal.created_at or now,
                "updated_at": proposal.updated_at or now,
            }
        )
        with self._engine.begin() as connection:
            existing = connection.execute(
                select(aion_action_proposals.c.action_proposal_id).where(
                    aion_action_proposals.c.action_proposal_id == stored.action_proposal_id
                )
            ).first()
            if existing is None:
                connection.execute(
                    insert(aion_action_proposals).values(**stored.model_dump(mode="python"))
                )
            else:
                connection.execute(
                    update(aion_action_proposals)
                    .where(aion_action_proposals.c.action_proposal_id == stored.action_proposal_id)
                    .values(**stored.model_dump(mode="python"))
                )
        return stored

    def get_proposal(self, action_proposal_id: str) -> ActionProposal | None:
        self._ensure_schema()
        with self._engine.connect() as connection:
            row = (
                connection.execute(
                    select(aion_action_proposals).where(
                        aion_action_proposals.c.action_proposal_id == action_proposal_id
                    )
                )
                .mappings()
                .first()
            )
        return ActionProposal(**dict(row)) if row is not None else None

    def list_proposals(self, query: ActionProposalQuery) -> list[ActionProposal]:
        self._ensure_schema()
        statement = select(aion_action_proposals).order_by(
            aion_action_proposals.c.created_at.desc()
        )
        if query.trace_id is not None:
            statement = statement.where(aion_action_proposals.c.trace_id == query.trace_id)
        if query.source_type is not None:
            statement = statement.where(aion_action_proposals.c.source_type == query.source_type)
        if query.source_id is not None:
            statement = statement.where(aion_action_proposals.c.source_id == query.source_id)
        if query.status is not None:
            statement = statement.where(aion_action_proposals.c.status == query.status)
        if query.proposal_type is not None:
            statement = statement.where(
                aion_action_proposals.c.proposal_type == query.proposal_type
            )
        if query.risk_level is not None:
            statement = statement.where(aion_action_proposals.c.risk_level == query.risk_level)
        if not query.include_deleted:
            statement = statement.where(aion_action_proposals.c.deleted_at.is_(None))
        statement = statement.limit(query.limit)
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
        return [
            ActionProposal(**dict(row))
            for row in rows
            if _scope_matches(row["owner_scope"], query.scope)
        ]

    def save_blocker(self, blocker: ActionBlocker) -> ActionBlocker:
        self._ensure_schema()
        stored = blocker.model_copy(update={"created_at": blocker.created_at or datetime.now(UTC)})
        with self._engine.begin() as connection:
            existing = connection.execute(
                select(aion_action_blockers.c.action_blocker_id).where(
                    aion_action_blockers.c.action_blocker_id == stored.action_blocker_id
                )
            ).first()
            if existing is None:
                connection.execute(
                    insert(aion_action_blockers).values(**stored.model_dump(mode="python"))
                )
            else:
                connection.execute(
                    update(aion_action_blockers)
                    .where(aion_action_blockers.c.action_blocker_id == stored.action_blocker_id)
                    .values(**stored.model_dump(mode="python"))
                )
        return stored

    def get_blocker(self, action_blocker_id: str) -> ActionBlocker | None:
        self._ensure_schema()
        with self._engine.connect() as connection:
            row = (
                connection.execute(
                    select(aion_action_blockers).where(
                        aion_action_blockers.c.action_blocker_id == action_blocker_id
                    )
                )
                .mappings()
                .first()
            )
        return ActionBlocker(**dict(row)) if row is not None else None

    def list_blockers(
        self,
        action_proposal_id: str | None = None,
        status: str | None = None,
        severity: str | None = None,
        limit: int = 100,
    ) -> list[ActionBlocker]:
        self._ensure_schema()
        statement = select(aion_action_blockers).order_by(aion_action_blockers.c.created_at.desc())
        if action_proposal_id is not None:
            statement = statement.where(
                aion_action_blockers.c.action_proposal_id == action_proposal_id
            )
        if status is not None:
            statement = statement.where(aion_action_blockers.c.status == status)
        if severity is not None:
            statement = statement.where(aion_action_blockers.c.severity == severity)
        statement = statement.limit(limit)
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
        return [ActionBlocker(**dict(row)) for row in rows]

    def save_review(self, review: ActionProposalReview) -> ActionProposalReview:
        self._ensure_schema()
        stored = review.model_copy(update={"created_at": review.created_at or datetime.now(UTC)})
        with self._engine.begin() as connection:
            connection.execute(
                insert(aion_action_proposal_reviews).values(**stored.model_dump(mode="python"))
            )
        return stored

    def list_reviews(
        self, action_proposal_id: str | None = None, decision: str | None = None, limit: int = 100
    ) -> list[ActionProposalReview]:
        self._ensure_schema()
        statement = select(aion_action_proposal_reviews).order_by(
            aion_action_proposal_reviews.c.created_at.desc()
        )
        if action_proposal_id is not None:
            statement = statement.where(
                aion_action_proposal_reviews.c.action_proposal_id == action_proposal_id
            )
        if decision is not None:
            statement = statement.where(aion_action_proposal_reviews.c.decision == decision)
        statement = statement.limit(limit)
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
        return [ActionProposalReview(**dict(row)) for row in rows]

    def save_handoff(self, handoff: ExecutionHandoff) -> ExecutionHandoff:
        self._ensure_schema()
        stored = handoff.model_copy(update={"created_at": handoff.created_at or datetime.now(UTC)})
        with self._engine.begin() as connection:
            connection.execute(
                insert(aion_execution_handoffs).values(**stored.model_dump(mode="python"))
            )
        return stored

    def get_handoff(self, execution_handoff_id: str) -> ExecutionHandoff | None:
        self._ensure_schema()
        with self._engine.connect() as connection:
            row = (
                connection.execute(
                    select(aion_execution_handoffs).where(
                        aion_execution_handoffs.c.execution_handoff_id == execution_handoff_id
                    )
                )
                .mappings()
                .first()
            )
        return ExecutionHandoff(**dict(row)) if row is not None else None

    def list_handoffs(
        self,
        action_proposal_id: str | None = None,
        status: str | None = None,
        target_system: str | None = None,
        limit: int = 100,
    ) -> list[ExecutionHandoff]:
        self._ensure_schema()
        statement = select(aion_execution_handoffs).order_by(
            aion_execution_handoffs.c.created_at.desc()
        )
        if action_proposal_id is not None:
            statement = statement.where(
                aion_execution_handoffs.c.action_proposal_id == action_proposal_id
            )
        if status is not None:
            statement = statement.where(aion_execution_handoffs.c.status == status)
        if target_system is not None:
            statement = statement.where(aion_execution_handoffs.c.target_system == target_system)
        statement = statement.limit(limit)
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
        return [ExecutionHandoff(**dict(row)) for row in rows]

    def save_tool_intent_review(self, review: ToolIntentReview) -> ToolIntentReview:
        self._ensure_schema()
        stored = review.model_copy(update={"created_at": review.created_at or datetime.now(UTC)})
        with self._engine.begin() as connection:
            connection.execute(
                insert(aion_tool_intent_reviews).values(**stored.model_dump(mode="python"))
            )
        return stored

    def list_tool_intent_reviews(
        self, tool_intent_id: str | None = None, status: str | None = None, limit: int = 100
    ) -> list[ToolIntentReview]:
        self._ensure_schema()
        statement = select(aion_tool_intent_reviews).order_by(
            aion_tool_intent_reviews.c.created_at.desc()
        )
        if tool_intent_id is not None:
            statement = statement.where(aion_tool_intent_reviews.c.tool_intent_id == tool_intent_id)
        if status is not None:
            statement = statement.where(aion_tool_intent_reviews.c.status == status)
        statement = statement.limit(limit)
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
        return [ToolIntentReview(**dict(row)) for row in rows]

    def query(self, query: ActionProposalQuery) -> ActionProposalQueryResult:
        proposals = self.list_proposals(query)
        proposal_ids = [proposal.action_proposal_id for proposal in proposals]
        reviews = [
            review
            for proposal_id in proposal_ids
            for review in self.list_reviews(action_proposal_id=proposal_id, limit=query.limit)
        ]
        blockers = [
            blocker
            for proposal_id in proposal_ids
            for blocker in self.list_blockers(action_proposal_id=proposal_id, limit=query.limit)
        ]
        handoffs = [
            handoff
            for proposal_id in proposal_ids
            for handoff in self.list_handoffs(action_proposal_id=proposal_id, limit=query.limit)
        ]
        tool_reviews = [
            review
            for review in self.list_tool_intent_reviews(limit=query.limit)
            if review.action_proposal_id in proposal_ids
        ]
        return ActionProposalQueryResult(
            proposals=proposals,
            reviews=reviews,
            blockers=blockers,
            handoffs=handoffs,
            tool_intent_reviews=tool_reviews,
            total_count=len(proposals),
            constraints=["proposals_do_not_execute"],
            metadata={"source": "action_proposal_repository"},
        )

    def _ensure_schema(self) -> None:
        if self._schema_ready:
            return
        if self._auto_create:
            action_proposal_metadata.create_all(self._engine)
        self._schema_ready = True


def _scope_matches(owner_scope: object, query_scope: list[str]) -> bool:
    if not isinstance(owner_scope, list):
        return True
    return bool(set(str(item) for item in owner_scope).intersection(query_scope))


__all__ = ["ActionProposalRepository"]
