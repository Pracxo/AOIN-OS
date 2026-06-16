"""Persistence for AION dialogue and response records."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, cast

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
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

from aion_brain.contracts.dialogue import (
    ClarificationRequest,
    DialogueFeedback,
    DialogueMessage,
    DialogueMessageType,
    DialogueRole,
    DialogueSession,
    DialogueSessionStatus,
    DialogueSessionType,
)
from aion_brain.contracts.responses import (
    ResponseDeliveryRecord,
    ResponseDraft,
    ResponseVerification,
)

dialogue_metadata = MetaData()
json_payload_type = JSON().with_variant(JSONB(), "postgresql")

aion_dialogue_sessions = Table(
    "aion_dialogue_sessions",
    dialogue_metadata,
    Column("dialogue_session_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("actor_id", Text, nullable=True),
    Column("workspace_id", Text, nullable=True),
    Column("status", Text, nullable=False),
    Column("session_type", Text, nullable=False),
    Column("title", Text, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("active_focus_session_id", Text, nullable=True),
    Column("active_goal_id", Text, nullable=True),
    Column("active_task_id", Text, nullable=True),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    Column("closed_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_dialogue_sessions_trace_id", "trace_id"),
    Index("ix_aion_dialogue_sessions_actor_id", "actor_id"),
    Index("ix_aion_dialogue_sessions_workspace_id", "workspace_id"),
    Index("ix_aion_dialogue_sessions_status", "status"),
    Index("ix_aion_dialogue_sessions_session_type", "session_type"),
    Index("ix_aion_dialogue_sessions_active_focus_session_id", "active_focus_session_id"),
    Index("ix_aion_dialogue_sessions_active_goal_id", "active_goal_id"),
    Index("ix_aion_dialogue_sessions_active_task_id", "active_task_id"),
    Index("ix_aion_dialogue_sessions_created_at", "created_at"),
)

aion_dialogue_messages = Table(
    "aion_dialogue_messages",
    dialogue_metadata,
    Column("message_id", Text, primary_key=True),
    Column(
        "dialogue_session_id",
        Text,
        ForeignKey("aion_dialogue_sessions.dialogue_session_id"),
        nullable=False,
    ),
    Column("trace_id", Text, nullable=True),
    Column("actor_id", Text, nullable=True),
    Column("workspace_id", Text, nullable=True),
    Column("role", Text, nullable=False),
    Column("message_type", Text, nullable=False),
    Column("content", Text, nullable=False),
    Column("content_hash", Text, nullable=False),
    Column("content_redacted", Boolean, nullable=False),
    Column("grounding_refs", json_payload_type, nullable=False),
    Column("memory_refs", json_payload_type, nullable=False),
    Column("evidence_refs", json_payload_type, nullable=False),
    Column("response_refs", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("deleted_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_dialogue_messages_dialogue_session_id", "dialogue_session_id"),
    Index("ix_aion_dialogue_messages_trace_id", "trace_id"),
    Index("ix_aion_dialogue_messages_actor_id", "actor_id"),
    Index("ix_aion_dialogue_messages_workspace_id", "workspace_id"),
    Index("ix_aion_dialogue_messages_role", "role"),
    Index("ix_aion_dialogue_messages_message_type", "message_type"),
    Index("ix_aion_dialogue_messages_content_hash", "content_hash"),
    Index("ix_aion_dialogue_messages_created_at", "created_at"),
    Index("ix_aion_dialogue_messages_deleted_at", "deleted_at"),
)

aion_clarification_requests = Table(
    "aion_clarification_requests",
    dialogue_metadata,
    Column("clarification_id", Text, primary_key=True),
    Column("dialogue_session_id", Text, nullable=True),
    Column("message_id", Text, nullable=True),
    Column("trace_id", Text, nullable=True),
    Column("status", Text, nullable=False),
    Column("question", Text, nullable=False),
    Column("reason", Text, nullable=False),
    Column("required", Boolean, nullable=False),
    Column("answer_message_id", Text, nullable=True),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("answered_at", DateTime(timezone=True), nullable=True),
    Column("cancelled_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_clarification_requests_dialogue_session_id", "dialogue_session_id"),
    Index("ix_aion_clarification_requests_message_id", "message_id"),
    Index("ix_aion_clarification_requests_trace_id", "trace_id"),
    Index("ix_aion_clarification_requests_status", "status"),
    Index("ix_aion_clarification_requests_required", "required"),
    Index("ix_aion_clarification_requests_created_at", "created_at"),
)

aion_response_drafts = Table(
    "aion_response_drafts",
    dialogue_metadata,
    Column("response_id", Text, primary_key=True),
    Column("dialogue_session_id", Text, nullable=True),
    Column("message_id", Text, nullable=True),
    Column("trace_id", Text, nullable=True),
    Column("reasoning_id", Text, nullable=True),
    Column("plan_id", Text, nullable=True),
    Column("status", Text, nullable=False),
    Column("response_type", Text, nullable=False),
    Column("content", Text, nullable=False),
    Column("content_hash", Text, nullable=False),
    Column("grounded", Boolean, nullable=False),
    Column("grounding_refs", json_payload_type, nullable=False),
    Column("memory_refs", json_payload_type, nullable=False),
    Column("evidence_refs", json_payload_type, nullable=False),
    Column("clarification_refs", json_payload_type, nullable=False),
    Column("constraints", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    Index("ix_aion_response_drafts_dialogue_session_id", "dialogue_session_id"),
    Index("ix_aion_response_drafts_message_id", "message_id"),
    Index("ix_aion_response_drafts_trace_id", "trace_id"),
    Index("ix_aion_response_drafts_reasoning_id", "reasoning_id"),
    Index("ix_aion_response_drafts_plan_id", "plan_id"),
    Index("ix_aion_response_drafts_status", "status"),
    Index("ix_aion_response_drafts_response_type", "response_type"),
    Index("ix_aion_response_drafts_grounded", "grounded"),
    Index("ix_aion_response_drafts_created_at", "created_at"),
)

aion_response_verifications = Table(
    "aion_response_verifications",
    dialogue_metadata,
    Column("verification_id", Text, primary_key=True),
    Column("response_id", Text, ForeignKey("aion_response_drafts.response_id"), nullable=False),
    Column("trace_id", Text, nullable=True),
    Column("status", Text, nullable=False),
    Column("grounded", Boolean, nullable=False),
    Column("policy_ok", Boolean, nullable=False),
    Column("autonomy_ok", Boolean, nullable=False),
    Column("approval_required", Boolean, nullable=False),
    Column("issues", json_payload_type, nullable=False),
    Column("score", Float, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Index("ix_aion_response_verifications_response_id", "response_id"),
    Index("ix_aion_response_verifications_trace_id", "trace_id"),
    Index("ix_aion_response_verifications_status", "status"),
    Index("ix_aion_response_verifications_grounded", "grounded"),
    Index("ix_aion_response_verifications_policy_ok", "policy_ok"),
    Index("ix_aion_response_verifications_autonomy_ok", "autonomy_ok"),
    Index("ix_aion_response_verifications_approval_required", "approval_required"),
    Index("ix_aion_response_verifications_score", "score"),
    Index("ix_aion_response_verifications_created_at", "created_at"),
)

aion_response_delivery_records = Table(
    "aion_response_delivery_records",
    dialogue_metadata,
    Column("delivery_id", Text, primary_key=True),
    Column("response_id", Text, ForeignKey("aion_response_drafts.response_id"), nullable=False),
    Column("dialogue_session_id", Text, nullable=True),
    Column("trace_id", Text, nullable=True),
    Column("delivery_type", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("delivered_to", Text, nullable=True),
    Column("output_channel", Text, nullable=False),
    Column("payload", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Index("ix_aion_response_delivery_records_response_id", "response_id"),
    Index("ix_aion_response_delivery_records_dialogue_session_id", "dialogue_session_id"),
    Index("ix_aion_response_delivery_records_trace_id", "trace_id"),
    Index("ix_aion_response_delivery_records_delivery_type", "delivery_type"),
    Index("ix_aion_response_delivery_records_status", "status"),
    Index("ix_aion_response_delivery_records_output_channel", "output_channel"),
    Index("ix_aion_response_delivery_records_created_at", "created_at"),
)

aion_dialogue_feedback = Table(
    "aion_dialogue_feedback",
    dialogue_metadata,
    Column("feedback_id", Text, primary_key=True),
    Column("dialogue_session_id", Text, nullable=True),
    Column("message_id", Text, nullable=True),
    Column("response_id", Text, nullable=True),
    Column("trace_id", Text, nullable=True),
    Column("actor_id", Text, nullable=True),
    Column("feedback_type", Text, nullable=False),
    Column("rating", Integer, nullable=True),
    Column("comment", Text, nullable=True),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Index("ix_aion_dialogue_feedback_dialogue_session_id", "dialogue_session_id"),
    Index("ix_aion_dialogue_feedback_message_id", "message_id"),
    Index("ix_aion_dialogue_feedback_response_id", "response_id"),
    Index("ix_aion_dialogue_feedback_trace_id", "trace_id"),
    Index("ix_aion_dialogue_feedback_actor_id", "actor_id"),
    Index("ix_aion_dialogue_feedback_feedback_type", "feedback_type"),
    Index("ix_aion_dialogue_feedback_rating", "rating"),
    Index("ix_aion_dialogue_feedback_created_at", "created_at"),
)


class DialogueRepository:
    """Repository for dialogue sessions, messages, responses, and feedback."""

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

    def save_session(self, session: DialogueSession) -> DialogueSession:
        self._ensure_schema()
        values = session.model_dump(mode="python")
        with self._engine.begin() as connection:
            existing = connection.execute(
                select(aion_dialogue_sessions.c.dialogue_session_id).where(
                    aion_dialogue_sessions.c.dialogue_session_id == session.dialogue_session_id
                )
            ).first()
            if existing is None:
                connection.execute(insert(aion_dialogue_sessions).values(**values))
            else:
                connection.execute(
                    update(aion_dialogue_sessions)
                    .where(
                        aion_dialogue_sessions.c.dialogue_session_id == session.dialogue_session_id
                    )
                    .values(**values)
                )
        return session

    def get_session(self, dialogue_session_id: str) -> DialogueSession | None:
        self._ensure_schema()
        row = self._first(
            select(aion_dialogue_sessions).where(
                aion_dialogue_sessions.c.dialogue_session_id == dialogue_session_id
            )
        )
        return _row_to_session(row) if row is not None else None

    def list_sessions(
        self,
        *,
        scope: list[str],
        status: str | None = None,
        session_type: str | None = None,
        limit: int = 50,
    ) -> list[DialogueSession]:
        self._ensure_schema()
        statement = select(aion_dialogue_sessions).order_by(
            aion_dialogue_sessions.c.created_at.desc()
        )
        if status is not None:
            statement = statement.where(aion_dialogue_sessions.c.status == status)
        if session_type is not None:
            statement = statement.where(aion_dialogue_sessions.c.session_type == session_type)
        return [
            session
            for session in (_row_to_session(row) for row in self._list(statement.limit(limit)))
            if _in_scope(session.owner_scope, scope)
        ][:limit]

    def save_message(self, message: DialogueMessage) -> DialogueMessage:
        self._ensure_schema()
        values = message.model_dump(mode="python")
        with self._engine.begin() as connection:
            connection.execute(insert(aion_dialogue_messages).values(**values))
        return message

    def get_message(self, message_id: str) -> DialogueMessage | None:
        self._ensure_schema()
        row = self._first(
            select(aion_dialogue_messages).where(aion_dialogue_messages.c.message_id == message_id)
        )
        return _row_to_message(row) if row is not None else None

    def list_messages(
        self,
        dialogue_session_id: str,
        *,
        include_deleted: bool = False,
        limit: int = 100,
    ) -> list[DialogueMessage]:
        self._ensure_schema()
        statement = (
            select(aion_dialogue_messages)
            .where(aion_dialogue_messages.c.dialogue_session_id == dialogue_session_id)
            .order_by(aion_dialogue_messages.c.created_at)
            .limit(limit)
        )
        if not include_deleted:
            statement = statement.where(aion_dialogue_messages.c.deleted_at.is_(None))
        return [_row_to_message(row) for row in self._list(statement)]

    def soft_delete_message(self, message_id: str, deleted_at: datetime) -> bool:
        self._ensure_schema()
        with self._engine.begin() as connection:
            result = connection.execute(
                update(aion_dialogue_messages)
                .where(aion_dialogue_messages.c.message_id == message_id)
                .values(deleted_at=deleted_at)
            )
        return result.rowcount > 0

    def save_clarification(self, clarification: ClarificationRequest) -> ClarificationRequest:
        self._ensure_schema()
        values = clarification.model_dump(mode="python")
        with self._engine.begin() as connection:
            existing = connection.execute(
                select(aion_clarification_requests.c.clarification_id).where(
                    aion_clarification_requests.c.clarification_id == clarification.clarification_id
                )
            ).first()
            if existing is None:
                connection.execute(insert(aion_clarification_requests).values(**values))
            else:
                connection.execute(
                    update(aion_clarification_requests)
                    .where(
                        aion_clarification_requests.c.clarification_id
                        == clarification.clarification_id
                    )
                    .values(**values)
                )
        return clarification

    def get_clarification(self, clarification_id: str) -> ClarificationRequest | None:
        self._ensure_schema()
        row = self._first(
            select(aion_clarification_requests).where(
                aion_clarification_requests.c.clarification_id == clarification_id
            )
        )
        return _row_to_clarification(row) if row is not None else None

    def list_pending_clarifications(
        self,
        *,
        dialogue_session_id: str | None = None,
        limit: int = 100,
    ) -> list[ClarificationRequest]:
        self._ensure_schema()
        statement = (
            select(aion_clarification_requests)
            .where(aion_clarification_requests.c.status == "pending")
            .order_by(aion_clarification_requests.c.created_at.desc())
            .limit(limit)
        )
        if dialogue_session_id is not None:
            statement = statement.where(
                aion_clarification_requests.c.dialogue_session_id == dialogue_session_id
            )
        return [_row_to_clarification(row) for row in self._list(statement)]

    def save_response(self, response: ResponseDraft) -> ResponseDraft:
        self._ensure_schema()
        values = response.model_dump(mode="python")
        with self._engine.begin() as connection:
            existing = connection.execute(
                select(aion_response_drafts.c.response_id).where(
                    aion_response_drafts.c.response_id == response.response_id
                )
            ).first()
            if existing is None:
                connection.execute(insert(aion_response_drafts).values(**values))
            else:
                connection.execute(
                    update(aion_response_drafts)
                    .where(aion_response_drafts.c.response_id == response.response_id)
                    .values(**values)
                )
        return response

    def get_response(self, response_id: str) -> ResponseDraft | None:
        self._ensure_schema()
        row = self._first(
            select(aion_response_drafts).where(aion_response_drafts.c.response_id == response_id)
        )
        return _row_to_response(row) if row is not None else None

    def list_blocked_responses(self, limit: int = 100) -> list[ResponseDraft]:
        self._ensure_schema()
        statement = (
            select(aion_response_drafts)
            .where(aion_response_drafts.c.status == "blocked")
            .order_by(aion_response_drafts.c.created_at.desc())
            .limit(limit)
        )
        return [_row_to_response(row) for row in self._list(statement)]

    def save_verification(self, verification: ResponseVerification) -> ResponseVerification:
        self._ensure_schema()
        values = verification.model_dump(mode="python")
        with self._engine.begin() as connection:
            connection.execute(insert(aion_response_verifications).values(**values))
        return verification

    def save_delivery(self, delivery: ResponseDeliveryRecord) -> ResponseDeliveryRecord:
        self._ensure_schema()
        values = delivery.model_dump(mode="python")
        with self._engine.begin() as connection:
            connection.execute(insert(aion_response_delivery_records).values(**values))
        return delivery

    def list_deliveries(
        self,
        *,
        response_id: str | None = None,
        dialogue_session_id: str | None = None,
        limit: int = 100,
    ) -> list[ResponseDeliveryRecord]:
        self._ensure_schema()
        statement = select(aion_response_delivery_records).order_by(
            aion_response_delivery_records.c.created_at.desc()
        )
        if response_id is not None:
            statement = statement.where(aion_response_delivery_records.c.response_id == response_id)
        if dialogue_session_id is not None:
            statement = statement.where(
                aion_response_delivery_records.c.dialogue_session_id == dialogue_session_id
            )
        return [_row_to_delivery(row) for row in self._list(statement.limit(limit))]

    def save_feedback(self, feedback: DialogueFeedback) -> DialogueFeedback:
        self._ensure_schema()
        values = feedback.model_dump(mode="python")
        with self._engine.begin() as connection:
            connection.execute(insert(aion_dialogue_feedback).values(**values))
        return feedback

    def list_feedback(
        self,
        *,
        dialogue_session_id: str | None = None,
        response_id: str | None = None,
        limit: int = 100,
    ) -> list[DialogueFeedback]:
        self._ensure_schema()
        statement = select(aion_dialogue_feedback).order_by(
            aion_dialogue_feedback.c.created_at.desc()
        )
        if dialogue_session_id is not None:
            statement = statement.where(
                aion_dialogue_feedback.c.dialogue_session_id == dialogue_session_id
            )
        if response_id is not None:
            statement = statement.where(aion_dialogue_feedback.c.response_id == response_id)
        return [_row_to_feedback(row) for row in self._list(statement.limit(limit))]

    def _ensure_schema(self) -> None:
        if self._schema_ready or not self._auto_create:
            return
        dialogue_metadata.create_all(self._engine)
        self._schema_ready = True

    def _first(self, statement: Any) -> RowMapping | None:
        with self._engine.connect() as connection:
            return connection.execute(statement).mappings().first()

    def _list(self, statement: Any) -> list[RowMapping]:
        with self._engine.connect() as connection:
            return list(connection.execute(statement).mappings().all())


def _row_to_session(row: RowMapping) -> DialogueSession:
    return DialogueSession(
        dialogue_session_id=str(row["dialogue_session_id"]),
        trace_id=_optional_str(row["trace_id"]),
        actor_id=_optional_str(row["actor_id"]),
        workspace_id=_optional_str(row["workspace_id"]),
        status=cast(DialogueSessionStatus, str(row["status"])),
        session_type=cast(DialogueSessionType, str(row["session_type"])),
        title=str(row["title"]),
        owner_scope=_string_list(row["owner_scope"]),
        active_focus_session_id=_optional_str(row["active_focus_session_id"]),
        active_goal_id=_optional_str(row["active_goal_id"]),
        active_task_id=_optional_str(row["active_task_id"]),
        metadata=dict(row["metadata"]),
        created_by=_optional_str(row["created_by"]),
        created_at=_datetime(row["created_at"]),
        updated_at=_datetime(row["updated_at"]),
        closed_at=_optional_datetime(row["closed_at"]),
    )


def _row_to_message(row: RowMapping) -> DialogueMessage:
    return DialogueMessage(
        message_id=str(row["message_id"]),
        dialogue_session_id=str(row["dialogue_session_id"]),
        trace_id=_optional_str(row["trace_id"]),
        actor_id=_optional_str(row["actor_id"]),
        workspace_id=_optional_str(row["workspace_id"]),
        role=cast(DialogueRole, str(row["role"])),
        message_type=cast(DialogueMessageType, str(row["message_type"])),
        content=str(row["content"]),
        content_hash=str(row["content_hash"]),
        content_redacted=bool(row["content_redacted"]),
        grounding_refs=_string_list(row["grounding_refs"]),
        memory_refs=_string_list(row["memory_refs"]),
        evidence_refs=_string_list(row["evidence_refs"]),
        response_refs=_string_list(row["response_refs"]),
        metadata=dict(row["metadata"]),
        created_at=_datetime(row["created_at"]),
        deleted_at=_optional_datetime(row["deleted_at"]),
    )


def _row_to_clarification(row: RowMapping) -> ClarificationRequest:
    return ClarificationRequest(
        clarification_id=str(row["clarification_id"]),
        dialogue_session_id=_optional_str(row["dialogue_session_id"]),
        message_id=_optional_str(row["message_id"]),
        trace_id=_optional_str(row["trace_id"]),
        status=cast(Any, str(row["status"])),
        question=str(row["question"]),
        reason=str(row["reason"]),
        required=bool(row["required"]),
        answer_message_id=_optional_str(row["answer_message_id"]),
        metadata=dict(row["metadata"]),
        created_at=_datetime(row["created_at"]),
        answered_at=_optional_datetime(row["answered_at"]),
        cancelled_at=_optional_datetime(row["cancelled_at"]),
    )


def _row_to_response(row: RowMapping) -> ResponseDraft:
    return ResponseDraft(
        response_id=str(row["response_id"]),
        dialogue_session_id=_optional_str(row["dialogue_session_id"]),
        message_id=_optional_str(row["message_id"]),
        trace_id=_optional_str(row["trace_id"]),
        reasoning_id=_optional_str(row["reasoning_id"]),
        plan_id=_optional_str(row["plan_id"]),
        status=cast(Any, str(row["status"])),
        response_type=cast(Any, str(row["response_type"])),
        content=str(row["content"]),
        content_hash=str(row["content_hash"]),
        grounded=bool(row["grounded"]),
        grounding_refs=_string_list(row["grounding_refs"]),
        memory_refs=_string_list(row["memory_refs"]),
        evidence_refs=_string_list(row["evidence_refs"]),
        clarification_refs=_string_list(row["clarification_refs"]),
        constraints=_string_list(row["constraints"]),
        metadata=dict(row["metadata"]),
        created_at=_datetime(row["created_at"]),
        updated_at=_datetime(row["updated_at"]),
    )


def _row_to_delivery(row: RowMapping) -> ResponseDeliveryRecord:
    return ResponseDeliveryRecord(
        delivery_id=str(row["delivery_id"]),
        response_id=str(row["response_id"]),
        dialogue_session_id=_optional_str(row["dialogue_session_id"]),
        trace_id=_optional_str(row["trace_id"]),
        delivery_type=cast(Any, str(row["delivery_type"])),
        status=cast(Any, str(row["status"])),
        delivered_to=_optional_str(row["delivered_to"]),
        output_channel=str(row["output_channel"]),
        payload=dict(row["payload"]),
        metadata=dict(row["metadata"]),
        created_at=_datetime(row["created_at"]),
    )


def _row_to_feedback(row: RowMapping) -> DialogueFeedback:
    return DialogueFeedback(
        feedback_id=str(row["feedback_id"]),
        dialogue_session_id=_optional_str(row["dialogue_session_id"]),
        message_id=_optional_str(row["message_id"]),
        response_id=_optional_str(row["response_id"]),
        trace_id=_optional_str(row["trace_id"]),
        actor_id=_optional_str(row["actor_id"]),
        feedback_type=cast(Any, str(row["feedback_type"])),
        rating=int(row["rating"]) if row["rating"] is not None else None,
        comment=_optional_str(row["comment"]),
        metadata=dict(row["metadata"]),
        created_at=_datetime(row["created_at"]),
    )


def _optional_str(value: Any) -> str | None:
    return None if value is None else str(value)


def _string_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value]
    return []


def _datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value
    raise TypeError("expected datetime")


def _optional_datetime(value: Any) -> datetime | None:
    return None if value is None else _datetime(value)


def _in_scope(owner_scope: list[str], requested_scope: list[str]) -> bool:
    return not owner_scope or not requested_scope or bool(set(owner_scope) & set(requested_scope))
