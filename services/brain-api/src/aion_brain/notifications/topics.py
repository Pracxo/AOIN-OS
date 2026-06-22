"""Notification topic service."""

from __future__ import annotations

from datetime import UTC, datetime

from aion_brain.contracts.notifications import NotificationTopic
from aion_brain.contracts.scopes import ActorContext
from aion_brain.dialogue._shared import authorize, emit_telemetry

DEFAULT_TOPICS: tuple[tuple[str, str, str, str, str], ...] = (
    ("operator.action.created", "Operator action created", "operator", "medium", "Operator item."),
    ("approval.pending", "Approval pending", "approval", "medium", "Approval requires review."),
    ("action.proposal.blocked", "Action proposal blocked", "action", "high", "Action blocked."),
    ("run.stalled", "Run stalled", "run_supervision", "high", "Run appears stalled."),
    ("run.timeout", "Run timeout", "run_supervision", "critical", "Run timed out."),
    ("model_output.blocked", "Model output blocked", "model_output", "high", "Output blocked."),
    ("prompt.injection.detected", "Prompt injection detected", "prompt", "high", "Prompt risk."),
    ("grounding.failed", "Grounding failed", "grounding", "high", "Grounding failed."),
    ("security.hardening.failed", "Hardening failed", "security", "critical", "Hardening failed."),
    (
        "audit.verification.failed",
        "Audit verification failed",
        "audit",
        "critical",
        "Audit failed.",
    ),
    ("resilience.degraded", "Resilience degraded", "resilience", "high", "Resilience degraded."),
    ("outcome.failed", "Outcome failed", "outcome", "high", "Outcome failed."),
    ("learning.pattern.high", "High learning pattern", "learning", "high", "Pattern needs review."),
    ("backup.failed", "Backup failed", "backup", "high", "Backup failed."),
    ("release.failed", "Release failed", "release", "high", "Release failed."),
    ("freeze.failed", "Freeze gate failed", "freeze", "high", "Freeze gate failed."),
    ("generic.info", "Generic info", "generic", "info", "Generic local notification."),
)


class NotificationTopicService:
    """Manage local notification topics."""

    def __init__(
        self,
        repository: object,
        policy_adapter: object | None,
        *,
        telemetry_service: object | None = None,
        actor_context: ActorContext | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._telemetry_service = telemetry_service
        self._actor_context = actor_context or ActorContext()

    def with_actor_context(self, actor_context: ActorContext) -> NotificationTopicService:
        return NotificationTopicService(
            self._repository,
            self._policy_adapter,
            telemetry_service=self._telemetry_service,
            actor_context=actor_context,
        )

    def create_topic(self, topic: NotificationTopic) -> NotificationTopic:
        authorize(
            self._policy_adapter,
            action_type="notification.topic.create",
            resource_type="notification_topic",
            resource_id=topic.topic_key,
            scope=topic.owner_scope,
            actor_id=topic.created_by or self._actor_context.actor_id,
            risk_level="medium",
        )
        stored = _save_topic(self._repository, topic)
        emit_telemetry(
            self._telemetry_service,
            event_type="notification_topic_created",
            node_type="notification_topic",
            node_id=stored.topic_id,
            intensity=0.3,
            trace_id=None,
            payload={"topic_key": stored.topic_key},
        )
        return stored

    def get_topic(self, topic_key: str, scope: list[str]) -> NotificationTopic | None:
        authorize(
            self._policy_adapter,
            action_type="notification.topic.read",
            resource_type="notification_topic",
            resource_id=topic_key,
            scope=scope,
            risk_level="low",
        )
        get = getattr(self._repository, "get_topic", None)
        topic = get(topic_key) if callable(get) else None
        if not isinstance(topic, NotificationTopic):
            return None
        return topic if _scope_matches(topic.owner_scope, scope) else None

    def list_topics(
        self,
        scope: list[str],
        status: str | None = None,
        category: str | None = None,
        limit: int = 100,
    ) -> list[NotificationTopic]:
        authorize(
            self._policy_adapter,
            action_type="notification.topic.read",
            resource_type="notification_topic",
            resource_id=None,
            scope=scope,
            risk_level="low",
        )
        list_topics = getattr(self._repository, "list_topics", None)
        if not callable(list_topics):
            return []
        result = list_topics(scope=scope, status=status, category=category, limit=limit)
        return [item for item in result if isinstance(item, NotificationTopic)]

    def disable_topic(self, topic_key: str, actor_id: str | None, reason: str) -> NotificationTopic:
        topic = self.get_topic(topic_key, self._actor_context.security_scope or ["workspace:main"])
        if topic is None:
            raise ValueError("notification_topic_not_found")
        authorize(
            self._policy_adapter,
            action_type="notification.topic.update",
            resource_type="notification_topic",
            resource_id=topic_key,
            scope=topic.owner_scope,
            actor_id=actor_id or self._actor_context.actor_id,
            risk_level="medium",
            context={"reason": reason},
        )
        return _save_topic(
            self._repository,
            topic.model_copy(
                update={
                    "status": "disabled",
                    "disabled_at": datetime.now(UTC),
                    "updated_at": datetime.now(UTC),
                    "metadata": {**topic.metadata, "disable_reason": reason},
                }
            ),
        )

    def seed_default_topics(self, scope: list[str], dry_run: bool = True) -> dict[str, object]:
        topics = [
            NotificationTopic(
                topic_id=f"topic-{key.replace('.', '-')}",
                topic_key=key,
                name=name,
                description=description,
                status="active",
                category=category,  # type: ignore[arg-type]
                severity_default=severity,  # type: ignore[arg-type]
                owner_scope=scope,
                metadata={"seeded_default": True},
                created_by=self._actor_context.actor_id,
            )
            for key, name, category, severity, description in DEFAULT_TOPICS
        ]
        if dry_run:
            return {
                "dry_run": True,
                "topic_count": len(topics),
                "topics": [t.topic_key for t in topics],
            }
        for topic in topics:
            self.create_topic(topic)
        return {
            "dry_run": False,
            "topic_count": len(topics),
            "topics": [t.topic_key for t in topics],
        }


def _save_topic(repository: object, topic: NotificationTopic) -> NotificationTopic:
    save = getattr(repository, "save_topic", None)
    stored = save(topic) if callable(save) else topic
    return stored if isinstance(stored, NotificationTopic) else topic


def _scope_matches(owner_scope: list[str], scope: list[str]) -> bool:
    return bool(set(owner_scope).intersection(scope))


__all__ = ["DEFAULT_TOPICS", "NotificationTopicService"]
