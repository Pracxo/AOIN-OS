"""Local escalation queue service."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from aion_brain.contracts.alerts import AlertRecord
from aion_brain.contracts.notifications import (
    EscalationPolicy,
    EscalationRecord,
    NotificationRecord,
)
from aion_brain.contracts.scopes import ActorContext
from aion_brain.dialogue._shared import authorize, emit_telemetry

_SEVERITY_RANK = {"info": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}


class EscalationService:
    """Evaluate local-only escalation policies."""

    def __init__(
        self,
        repository: object,
        policy_adapter: object | None,
        *,
        telemetry_service: object | None = None,
        settings: object | None = None,
        actor_context: ActorContext | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._telemetry_service = telemetry_service
        self._settings = settings
        self._actor_context = actor_context or ActorContext()

    def with_actor_context(self, actor_context: ActorContext) -> EscalationService:
        return EscalationService(
            self._repository,
            self._policy_adapter,
            telemetry_service=self._telemetry_service,
            settings=self._settings,
            actor_context=actor_context,
        )

    def create_policy(self, policy: EscalationPolicy) -> EscalationPolicy:
        authorize(
            self._policy_adapter,
            action_type="escalation.policy.create",
            resource_type="escalation_policy",
            resource_id=policy.escalation_policy_id,
            scope=policy.owner_scope,
            actor_id=policy.created_by or self._actor_context.actor_id,
            risk_level="medium",
        )
        return _save_policy(self._repository, policy)

    def list_policies(
        self,
        scope: list[str],
        status: str | None = None,
        topic_key: str | None = None,
        alert_type: str | None = None,
        limit: int = 100,
    ) -> list[EscalationPolicy]:
        authorize(
            self._policy_adapter,
            action_type="escalation.policy.read",
            resource_type="escalation_policy",
            resource_id=None,
            scope=scope,
            risk_level="low",
        )
        list_policies = getattr(self._repository, "list_escalation_policies", None)
        if not callable(list_policies):
            return []
        result = list_policies(
            scope=scope,
            status=status,
            topic_key=topic_key,
            alert_type=alert_type,
            limit=limit,
        )
        return [item for item in result if isinstance(item, EscalationPolicy)]

    def disable_policy(
        self, escalation_policy_id: str, actor_id: str | None, reason: str
    ) -> EscalationPolicy:
        policy = _require_policy(self._repository, escalation_policy_id)
        authorize(
            self._policy_adapter,
            action_type="escalation.policy.update",
            resource_type="escalation_policy",
            resource_id=escalation_policy_id,
            scope=policy.owner_scope,
            actor_id=actor_id or self._actor_context.actor_id,
            risk_level="medium",
            context={"reason": reason},
        )
        return _save_policy(
            self._repository,
            policy.model_copy(
                update={
                    "status": "disabled",
                    "disabled_at": datetime.now(UTC),
                    "updated_at": datetime.now(UTC),
                    "metadata": {**policy.metadata, "disable_reason": reason},
                }
            ),
        )

    def evaluate(
        self,
        alert_id: str | None = None,
        notification_id: str | None = None,
        scope: list[str] | None = None,
    ) -> list[EscalationRecord]:
        scope = scope or self._actor_context.security_scope or ["workspace:main"]
        authorize(
            self._policy_adapter,
            action_type="escalation.evaluate",
            resource_type="escalation_record",
            resource_id=alert_id or notification_id,
            scope=scope,
            risk_level="medium",
        )
        alert = _get_alert(self._repository, alert_id) if alert_id else None
        notification = (
            _get_notification(self._repository, notification_id) if notification_id else None
        )
        if alert is None and notification is None:
            return []
        severity = alert.severity if alert else notification.severity  # type: ignore[union-attr]
        topic_key = notification.topic_key if notification else None
        alert_type = alert.alert_type if alert else None
        policies = self.list_policies(scope, status="active", topic_key=topic_key, limit=100)
        policies.extend(
            policy
            for policy in self.list_policies(
                scope, status="active", alert_type=alert_type, limit=100
            )
            if policy not in policies
        )
        records: list[EscalationRecord] = []
        for policy in policies:
            if _SEVERITY_RANK.get(policy.severity_threshold, 0) > _SEVERITY_RANK.get(severity, 0):
                continue
            if (
                _repeat_count(self._repository, policy, alert_id, notification_id)
                >= policy.repeat_limit
            ):
                continue
            record = EscalationRecord(
                escalation_record_id=f"escalation-{uuid4().hex}",
                trace_id=(alert.trace_id if alert else notification.trace_id),  # type: ignore[union-attr]
                alert_id=alert_id,
                notification_id=notification_id,
                escalation_policy_id=policy.escalation_policy_id,
                status="delivered_local",
                severity=severity,
                escalation_channel=policy.escalation_channel,
                escalation_target=policy.escalation_target,
                reason="local_escalation_policy_matched",
                local_only=True,
                result={"delivered_local": True, "external_delivery": False},
                metadata={"policy_name": policy.name},
                created_by=self._actor_context.actor_id,
                created_at=datetime.now(UTC),
            )
            stored = _save_record(self._repository, record)
            records.append(stored)
            emit_telemetry(
                self._telemetry_service,
                event_type="escalation_record_created",
                node_type="escalation",
                node_id=stored.escalation_record_id,
                intensity=1.0 if stored.severity == "critical" else 0.7,
                trace_id=stored.trace_id,
                payload={"severity": stored.severity},
            )
        return records

    def list_records(
        self,
        scope: list[str],
        status: str | None = None,
        severity: str | None = None,
        limit: int = 100,
    ) -> list[EscalationRecord]:
        authorize(
            self._policy_adapter,
            action_type="escalation.read",
            resource_type="escalation_record",
            resource_id=None,
            scope=scope,
            risk_level="low",
        )
        list_records = getattr(self._repository, "list_escalation_records", None)
        if not callable(list_records):
            return []
        result = list_records(scope=scope, status=status, severity=severity, limit=limit)
        return [item for item in result if isinstance(item, EscalationRecord)]

    def acknowledge(
        self, escalation_record_id: str, actor_id: str | None, reason: str
    ) -> EscalationRecord:
        return self._update(escalation_record_id, actor_id, reason, "acknowledged")

    def resolve(
        self, escalation_record_id: str, actor_id: str | None, reason: str
    ) -> EscalationRecord:
        return self._update(escalation_record_id, actor_id, reason, "resolved")

    def _update(
        self, escalation_record_id: str, actor_id: str | None, reason: str, status: str
    ) -> EscalationRecord:
        record = _require_record(self._repository, escalation_record_id)
        authorize(
            self._policy_adapter,
            action_type="escalation.update",
            resource_type="escalation_record",
            resource_id=escalation_record_id,
            scope=self._actor_context.security_scope or ["workspace:main"],
            actor_id=actor_id or self._actor_context.actor_id,
            risk_level="medium",
            context={"reason": reason, "status": status},
        )
        update: dict[str, object] = {
            "status": status,
            "metadata": {**record.metadata, f"{status}_reason": reason},
        }
        if status == "acknowledged":
            update["acknowledged_at"] = datetime.now(UTC)
        if status == "resolved":
            update["resolved_at"] = datetime.now(UTC)
        return _save_record(self._repository, record.model_copy(update=update))


def _save_policy(repository: object, policy: EscalationPolicy) -> EscalationPolicy:
    save = getattr(repository, "save_escalation_policy", None)
    stored = save(policy) if callable(save) else policy
    return stored if isinstance(stored, EscalationPolicy) else policy


def _save_record(repository: object, record: EscalationRecord) -> EscalationRecord:
    save = getattr(repository, "save_escalation_record", None)
    stored = save(record) if callable(save) else record
    return stored if isinstance(stored, EscalationRecord) else record


def _require_policy(repository: object, escalation_policy_id: str) -> EscalationPolicy:
    get = getattr(repository, "get_escalation_policy", None)
    policy = get(escalation_policy_id) if callable(get) else None
    if not isinstance(policy, EscalationPolicy):
        raise ValueError("escalation_policy_not_found")
    return policy


def _require_record(repository: object, escalation_record_id: str) -> EscalationRecord:
    get = getattr(repository, "get_escalation_record", None)
    record = get(escalation_record_id) if callable(get) else None
    if not isinstance(record, EscalationRecord):
        raise ValueError("escalation_record_not_found")
    return record


def _get_alert(repository: object, alert_id: str | None) -> AlertRecord | None:
    if alert_id is None:
        return None
    get = getattr(repository, "get_alert", None)
    alert = get(alert_id) if callable(get) else None
    return alert if isinstance(alert, AlertRecord) else None


def _get_notification(repository: object, notification_id: str | None) -> NotificationRecord | None:
    if notification_id is None:
        return None
    get = getattr(repository, "get_notification", None)
    notification = get(notification_id) if callable(get) else None
    return notification if isinstance(notification, NotificationRecord) else None


def _repeat_count(
    repository: object,
    policy: EscalationPolicy,
    alert_id: str | None,
    notification_id: str | None,
) -> int:
    list_records = getattr(repository, "list_escalation_records", None)
    if not callable(list_records):
        return 0
    return len(
        list_records(
            escalation_policy_id=policy.escalation_policy_id,
            alert_id=alert_id,
            notification_id=notification_id,
            limit=100,
        )
    )


__all__ = ["EscalationService"]
