"""Persistent repository for local notifications and alerts."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
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
from sqlalchemy.engine import Engine
from sqlalchemy.pool import QueuePool, StaticPool
from sqlalchemy.types import JSON

from aion_brain.contracts.alerts import AlertRecord
from aion_brain.contracts.notifications import (
    EscalationPolicy,
    EscalationRecord,
    NotificationDigest,
    NotificationRecord,
    NotificationSubscription,
    NotificationTopic,
)

notification_metadata = MetaData()
json_payload_type = JSON().with_variant(JSONB(), "postgresql")

aion_notification_topics = Table(
    "aion_notification_topics",
    notification_metadata,
    Column("topic_id", Text, primary_key=True),
    Column("topic_key", Text, nullable=False, unique=True),
    Column("name", Text, nullable=False),
    Column("description", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("category", Text, nullable=False),
    Column("severity_default", Text, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    Column("disabled_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_notification_topics_topic_key", "topic_key"),
    Index("ix_aion_notification_topics_status", "status"),
    Index("ix_aion_notification_topics_category", "category"),
    Index("ix_aion_notification_topics_severity_default", "severity_default"),
    Index("ix_aion_notification_topics_created_at", "created_at"),
)

aion_notification_subscriptions = Table(
    "aion_notification_subscriptions",
    notification_metadata,
    Column("subscription_id", Text, primary_key=True),
    Column("topic_key", Text, nullable=False),
    Column("actor_id", Text, nullable=True),
    Column("workspace_id", Text, nullable=True),
    Column("subscriber_type", Text, nullable=False),
    Column("subscriber_ref", Text, nullable=False),
    Column("channel", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("severity_threshold", Text, nullable=False),
    Column("filters", json_payload_type, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    Column("disabled_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_notification_subscriptions_topic_key", "topic_key"),
    Index("ix_aion_notification_subscriptions_actor_id", "actor_id"),
    Index("ix_aion_notification_subscriptions_workspace_id", "workspace_id"),
    Index("ix_aion_notification_subscriptions_subscriber_type", "subscriber_type"),
    Index("ix_aion_notification_subscriptions_channel", "channel"),
    Index("ix_aion_notification_subscriptions_status", "status"),
    Index("ix_aion_notification_subscriptions_severity_threshold", "severity_threshold"),
    Index("ix_aion_notification_subscriptions_created_at", "created_at"),
)

aion_notifications = Table(
    "aion_notifications",
    notification_metadata,
    Column("notification_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("actor_id", Text, nullable=True),
    Column("workspace_id", Text, nullable=True),
    Column("topic_key", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("severity", Text, nullable=False),
    Column("title", Text, nullable=False),
    Column("message", Text, nullable=False),
    Column("source_type", Text, nullable=False),
    Column("source_id", Text, nullable=True),
    Column("target_type", Text, nullable=True),
    Column("target_id", Text, nullable=True),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("refs", json_payload_type, nullable=False),
    Column("delivery_channels", json_payload_type, nullable=False),
    Column("delivered_to", json_payload_type, nullable=False),
    Column("read_by", json_payload_type, nullable=False),
    Column("acknowledged_by", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("read_at", DateTime(timezone=True), nullable=True),
    Column("acknowledged_at", DateTime(timezone=True), nullable=True),
    Column("resolved_at", DateTime(timezone=True), nullable=True),
    Column("archived_at", DateTime(timezone=True), nullable=True),
    Column("deleted_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_notifications_trace_id", "trace_id"),
    Index("ix_aion_notifications_actor_id", "actor_id"),
    Index("ix_aion_notifications_workspace_id", "workspace_id"),
    Index("ix_aion_notifications_topic_key", "topic_key"),
    Index("ix_aion_notifications_status", "status"),
    Index("ix_aion_notifications_severity", "severity"),
    Index("ix_aion_notifications_source_type", "source_type"),
    Index("ix_aion_notifications_source_id", "source_id"),
    Index("ix_aion_notifications_target_type", "target_type"),
    Index("ix_aion_notifications_target_id", "target_id"),
    Index("ix_aion_notifications_created_at", "created_at"),
    Index("ix_aion_notifications_deleted_at", "deleted_at"),
)

aion_alerts = Table(
    "aion_alerts",
    notification_metadata,
    Column("alert_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("actor_id", Text, nullable=True),
    Column("workspace_id", Text, nullable=True),
    Column("alert_type", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("severity", Text, nullable=False),
    Column("title", Text, nullable=False),
    Column("description", Text, nullable=False),
    Column("source_type", Text, nullable=False),
    Column("source_id", Text, nullable=True),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("notification_ids", json_payload_type, nullable=False),
    Column("blocker_refs", json_payload_type, nullable=False),
    Column("run_refs", json_payload_type, nullable=False),
    Column("action_refs", json_payload_type, nullable=False),
    Column("evidence_refs", json_payload_type, nullable=False),
    Column("audit_refs", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("acknowledged_at", DateTime(timezone=True), nullable=True),
    Column("resolved_at", DateTime(timezone=True), nullable=True),
    Column("archived_at", DateTime(timezone=True), nullable=True),
    Column("deleted_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_alerts_trace_id", "trace_id"),
    Index("ix_aion_alerts_actor_id", "actor_id"),
    Index("ix_aion_alerts_workspace_id", "workspace_id"),
    Index("ix_aion_alerts_alert_type", "alert_type"),
    Index("ix_aion_alerts_status", "status"),
    Index("ix_aion_alerts_severity", "severity"),
    Index("ix_aion_alerts_source_type", "source_type"),
    Index("ix_aion_alerts_source_id", "source_id"),
    Index("ix_aion_alerts_created_at", "created_at"),
    Index("ix_aion_alerts_deleted_at", "deleted_at"),
)

aion_escalation_policies = Table(
    "aion_escalation_policies",
    notification_metadata,
    Column("escalation_policy_id", Text, primary_key=True),
    Column("name", Text, nullable=False, unique=True),
    Column("description", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("topic_key", Text, nullable=True),
    Column("alert_type", Text, nullable=True),
    Column("severity_threshold", Text, nullable=False),
    Column("delay_seconds", Integer, nullable=False),
    Column("repeat_limit", Integer, nullable=False),
    Column("escalation_channel", Text, nullable=False),
    Column("escalation_target", Text, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("conditions", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    Column("disabled_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_escalation_policies_name", "name"),
    Index("ix_aion_escalation_policies_status", "status"),
    Index("ix_aion_escalation_policies_topic_key", "topic_key"),
    Index("ix_aion_escalation_policies_alert_type", "alert_type"),
    Index("ix_aion_escalation_policies_severity_threshold", "severity_threshold"),
    Index("ix_aion_escalation_policies_escalation_channel", "escalation_channel"),
    Index("ix_aion_escalation_policies_created_at", "created_at"),
)

aion_escalation_records = Table(
    "aion_escalation_records",
    notification_metadata,
    Column("escalation_record_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("alert_id", Text, nullable=True),
    Column("notification_id", Text, nullable=True),
    Column("escalation_policy_id", Text, nullable=True),
    Column("status", Text, nullable=False),
    Column("severity", Text, nullable=False),
    Column("escalation_channel", Text, nullable=False),
    Column("escalation_target", Text, nullable=False),
    Column("reason", Text, nullable=False),
    Column("local_only", Boolean, nullable=False),
    Column("result", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("acknowledged_at", DateTime(timezone=True), nullable=True),
    Column("resolved_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_escalation_records_trace_id", "trace_id"),
    Index("ix_aion_escalation_records_alert_id", "alert_id"),
    Index("ix_aion_escalation_records_notification_id", "notification_id"),
    Index("ix_aion_escalation_records_policy_id", "escalation_policy_id"),
    Index("ix_aion_escalation_records_status", "status"),
    Index("ix_aion_escalation_records_severity", "severity"),
    Index("ix_aion_escalation_records_channel", "escalation_channel"),
    Index("ix_aion_escalation_records_local_only", "local_only"),
    Index("ix_aion_escalation_records_created_at", "created_at"),
)

aion_notification_digests = Table(
    "aion_notification_digests",
    notification_metadata,
    Column("digest_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("actor_id", Text, nullable=True),
    Column("workspace_id", Text, nullable=True),
    Column("digest_type", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("title", Text, nullable=False),
    Column("summary", Text, nullable=False),
    Column("notification_ids", json_payload_type, nullable=False),
    Column("alert_ids", json_payload_type, nullable=False),
    Column("counts", json_payload_type, nullable=False),
    Column("recommendations", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Index("ix_aion_notification_digests_trace_id", "trace_id"),
    Index("ix_aion_notification_digests_actor_id", "actor_id"),
    Index("ix_aion_notification_digests_workspace_id", "workspace_id"),
    Index("ix_aion_notification_digests_digest_type", "digest_type"),
    Index("ix_aion_notification_digests_status", "status"),
    Index("ix_aion_notification_digests_created_at", "created_at"),
)


class NotificationRepository:
    """Repository for local notification, alert, escalation, and digest records."""

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

    def save_topic(self, topic: NotificationTopic) -> NotificationTopic:
        now = datetime.now(UTC)
        stored = topic.model_copy(
            update={"created_at": topic.created_at or now, "updated_at": topic.updated_at or now}
        )
        self._upsert(aion_notification_topics, "topic_id", stored)
        return stored

    def get_topic(self, topic_key: str) -> NotificationTopic | None:
        self._ensure_schema()
        with self._engine.connect() as connection:
            row = (
                connection.execute(
                    select(aion_notification_topics).where(
                        aion_notification_topics.c.topic_key == topic_key
                    )
                )
                .mappings()
                .first()
            )
        return NotificationTopic(**dict(row)) if row is not None else None

    def list_topics(
        self,
        *,
        scope: list[str],
        status: str | None = None,
        category: str | None = None,
        limit: int = 100,
    ) -> list[NotificationTopic]:
        self._ensure_schema()
        statement = select(aion_notification_topics).order_by(
            aion_notification_topics.c.created_at.desc()
        )
        if status is not None:
            statement = statement.where(aion_notification_topics.c.status == status)
        if category is not None:
            statement = statement.where(aion_notification_topics.c.category == category)
        statement = statement.limit(limit)
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
        return [
            NotificationTopic(**dict(row))
            for row in rows
            if _scope_matches(row["owner_scope"], scope)
        ]

    def save_subscription(self, subscription: NotificationSubscription) -> NotificationSubscription:
        now = datetime.now(UTC)
        stored = subscription.model_copy(
            update={
                "created_at": subscription.created_at or now,
                "updated_at": subscription.updated_at or now,
            }
        )
        self._upsert(aion_notification_subscriptions, "subscription_id", stored)
        return stored

    def get_subscription(self, subscription_id: str) -> NotificationSubscription | None:
        row = self._get(aion_notification_subscriptions, "subscription_id", subscription_id)
        return NotificationSubscription(**row) if row is not None else None

    def list_subscriptions(
        self,
        *,
        scope: list[str],
        topic_key: str | None = None,
        actor_id: str | None = None,
        workspace_id: str | None = None,
        status: str | None = None,
        limit: int = 100,
    ) -> list[NotificationSubscription]:
        self._ensure_schema()
        statement = select(aion_notification_subscriptions).order_by(
            aion_notification_subscriptions.c.created_at.desc()
        )
        if topic_key is not None:
            statement = statement.where(aion_notification_subscriptions.c.topic_key == topic_key)
        if actor_id is not None:
            statement = statement.where(aion_notification_subscriptions.c.actor_id == actor_id)
        if workspace_id is not None:
            statement = statement.where(
                aion_notification_subscriptions.c.workspace_id == workspace_id
            )
        if status is not None:
            statement = statement.where(aion_notification_subscriptions.c.status == status)
        statement = statement.limit(limit)
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
        return [
            NotificationSubscription(**dict(row))
            for row in rows
            if _scope_matches(row["owner_scope"], scope)
        ]

    def save_notification(self, notification: NotificationRecord) -> NotificationRecord:
        stored = notification.model_copy(
            update={"created_at": notification.created_at or datetime.now(UTC)}
        )
        self._upsert(aion_notifications, "notification_id", stored)
        return stored

    def get_notification(self, notification_id: str) -> NotificationRecord | None:
        row = self._get(aion_notifications, "notification_id", notification_id)
        return NotificationRecord(**row) if row is not None else None

    def list_notifications(
        self,
        *,
        scope: list[str],
        trace_id: str | None = None,
        actor_id: str | None = None,
        workspace_id: str | None = None,
        topic_key: str | None = None,
        status: str | None = None,
        severity: str | None = None,
        source_type: str | None = None,
        source_id: str | None = None,
        include_deleted: bool = False,
        limit: int = 50,
    ) -> list[NotificationRecord]:
        self._ensure_schema()
        statement = select(aion_notifications).order_by(aion_notifications.c.created_at.desc())
        filters = {
            "trace_id": trace_id,
            "actor_id": actor_id,
            "workspace_id": workspace_id,
            "topic_key": topic_key,
            "status": status,
            "severity": severity,
            "source_type": source_type,
            "source_id": source_id,
        }
        for column, value in filters.items():
            if value is not None:
                statement = statement.where(getattr(aion_notifications.c, column) == value)
        if not include_deleted:
            statement = statement.where(aion_notifications.c.deleted_at.is_(None))
        statement = statement.limit(limit)
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
        return [
            NotificationRecord(**dict(row))
            for row in rows
            if _scope_matches(row["owner_scope"], scope)
        ]

    def save_alert(self, alert: AlertRecord) -> AlertRecord:
        stored = alert.model_copy(update={"created_at": alert.created_at or datetime.now(UTC)})
        self._upsert(aion_alerts, "alert_id", stored)
        return stored

    def get_alert(self, alert_id: str) -> AlertRecord | None:
        row = self._get(aion_alerts, "alert_id", alert_id)
        return AlertRecord(**row) if row is not None else None

    def list_alerts(
        self,
        *,
        scope: list[str],
        trace_id: str | None = None,
        alert_type: str | None = None,
        status: str | None = None,
        severity: str | None = None,
        source_type: str | None = None,
        source_id: str | None = None,
        include_deleted: bool = False,
        limit: int = 50,
    ) -> list[AlertRecord]:
        self._ensure_schema()
        statement = select(aion_alerts).order_by(aion_alerts.c.created_at.desc())
        filters = {
            "trace_id": trace_id,
            "alert_type": alert_type,
            "status": status,
            "severity": severity,
            "source_type": source_type,
            "source_id": source_id,
        }
        for column, value in filters.items():
            if value is not None:
                statement = statement.where(getattr(aion_alerts.c, column) == value)
        if not include_deleted:
            statement = statement.where(aion_alerts.c.deleted_at.is_(None))
        statement = statement.limit(limit)
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
        return [
            AlertRecord(**dict(row)) for row in rows if _scope_matches(row["owner_scope"], scope)
        ]

    def save_escalation_policy(self, policy: EscalationPolicy) -> EscalationPolicy:
        now = datetime.now(UTC)
        stored = policy.model_copy(
            update={"created_at": policy.created_at or now, "updated_at": policy.updated_at or now}
        )
        self._upsert(aion_escalation_policies, "escalation_policy_id", stored)
        return stored

    def get_escalation_policy(self, escalation_policy_id: str) -> EscalationPolicy | None:
        row = self._get(aion_escalation_policies, "escalation_policy_id", escalation_policy_id)
        return EscalationPolicy(**row) if row is not None else None

    def list_escalation_policies(
        self,
        *,
        scope: list[str],
        status: str | None = None,
        topic_key: str | None = None,
        alert_type: str | None = None,
        limit: int = 100,
    ) -> list[EscalationPolicy]:
        self._ensure_schema()
        statement = select(aion_escalation_policies).order_by(
            aion_escalation_policies.c.created_at.desc()
        )
        if status is not None:
            statement = statement.where(aion_escalation_policies.c.status == status)
        if topic_key is not None:
            statement = statement.where(aion_escalation_policies.c.topic_key == topic_key)
        if alert_type is not None:
            statement = statement.where(aion_escalation_policies.c.alert_type == alert_type)
        statement = statement.limit(limit)
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
        return [
            EscalationPolicy(**dict(row))
            for row in rows
            if _scope_matches(row["owner_scope"], scope)
        ]

    def save_escalation_record(self, record: EscalationRecord) -> EscalationRecord:
        stored = record.model_copy(update={"created_at": record.created_at or datetime.now(UTC)})
        self._upsert(aion_escalation_records, "escalation_record_id", stored)
        return stored

    def get_escalation_record(self, escalation_record_id: str) -> EscalationRecord | None:
        row = self._get(aion_escalation_records, "escalation_record_id", escalation_record_id)
        return EscalationRecord(**row) if row is not None else None

    def list_escalation_records(
        self,
        *,
        scope: list[str] | None = None,
        alert_id: str | None = None,
        notification_id: str | None = None,
        escalation_policy_id: str | None = None,
        status: str | None = None,
        severity: str | None = None,
        limit: int = 100,
    ) -> list[EscalationRecord]:
        self._ensure_schema()
        statement = select(aion_escalation_records).order_by(
            aion_escalation_records.c.created_at.desc()
        )
        filters = {
            "alert_id": alert_id,
            "notification_id": notification_id,
            "escalation_policy_id": escalation_policy_id,
            "status": status,
            "severity": severity,
        }
        for column, value in filters.items():
            if value is not None:
                statement = statement.where(getattr(aion_escalation_records.c, column) == value)
        statement = statement.limit(limit)
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
        records = [EscalationRecord(**dict(row)) for row in rows]
        return records if scope is None else records

    def save_digest(self, digest: NotificationDigest) -> NotificationDigest:
        stored = digest.model_copy(update={"created_at": digest.created_at or datetime.now(UTC)})
        self._upsert(aion_notification_digests, "digest_id", stored)
        return stored

    def list_digests(
        self, *, scope: list[str], digest_type: str | None = None, limit: int = 50
    ) -> list[NotificationDigest]:
        self._ensure_schema()
        statement = select(aion_notification_digests).order_by(
            aion_notification_digests.c.created_at.desc()
        )
        if digest_type is not None:
            statement = statement.where(aion_notification_digests.c.digest_type == digest_type)
        statement = statement.limit(limit)
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
        return [
            NotificationDigest(**dict(row))
            for row in rows
            if _scope_matches(row["owner_scope"], scope)
        ]

    def _upsert(self, table: Table, id_column: str, model: object) -> None:
        self._ensure_schema()
        values = model.model_dump(mode="python")  # type: ignore[attr-defined]
        with self._engine.begin() as connection:
            existing = connection.execute(
                select(getattr(table.c, id_column)).where(
                    getattr(table.c, id_column) == values[id_column]
                )
            ).first()
            if existing is None:
                connection.execute(insert(table).values(**values))
            else:
                connection.execute(
                    update(table)
                    .where(getattr(table.c, id_column) == values[id_column])
                    .values(**values)
                )

    def _get(self, table: Table, id_column: str, value: str) -> dict[str, Any] | None:
        self._ensure_schema()
        with self._engine.connect() as connection:
            row = (
                connection.execute(select(table).where(getattr(table.c, id_column) == value))
                .mappings()
                .first()
            )
        return dict(row) if row is not None else None

    def _ensure_schema(self) -> None:
        if self._schema_ready:
            return
        if self._auto_create:
            notification_metadata.create_all(self._engine)
        self._schema_ready = True


def _scope_matches(owner_scope: object, query_scope: list[str]) -> bool:
    if not isinstance(owner_scope, list):
        return False
    return bool(set(str(item) for item in owner_scope).intersection(query_scope))


__all__ = ["NotificationRepository", "notification_metadata"]
