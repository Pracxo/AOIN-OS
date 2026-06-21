"""Notification and alert contract tests."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from aion_brain.contracts.alerts import AlertCreateRequest
from aion_brain.contracts.notifications import (
    EscalationRecord,
    NotificationDigest,
    NotificationRecord,
    NotificationSubscription,
    NotificationTopic,
)


def test_notification_topic_requires_dotted_key_and_scope() -> None:
    topic = NotificationTopic(
        topic_id="topic-1",
        topic_key="operator.action",
        name="Operator Action",
        description="Local operator notification topic.",
        status="active",
        category="operator",
        severity_default="medium",
        owner_scope=["workspace:main"],
    )

    assert topic.topic_key == "operator.action"

    with pytest.raises(ValidationError):
        NotificationTopic(
            topic_id="topic-2",
            topic_key="OperatorAction",
            name="Invalid",
            description="Invalid topic.",
            status="active",
            category="operator",
            severity_default="medium",
            owner_scope=["workspace:main"],
        )

    with pytest.raises(ValidationError):
        NotificationTopic(
            topic_id="topic-3",
            topic_key="operator.empty",
            name="Invalid",
            description="Invalid scope.",
            status="active",
            category="operator",
            severity_default="medium",
            owner_scope=[],
        )


def test_subscription_rejects_external_channel() -> None:
    with pytest.raises(ValidationError):
        NotificationSubscription(
            subscription_id="sub-1",
            topic_key="operator.action",
            subscriber_type="operator",
            subscriber_ref="operator",
            channel="email",
            status="active",
            severity_threshold="medium",
            owner_scope=["workspace:main"],
        )


def test_notification_record_rejects_hidden_reasoning_and_secret_metadata() -> None:
    with pytest.raises(ValidationError):
        NotificationRecord(
            notification_id="notification-1",
            topic_key="operator.action",
            status="delivered",
            severity="medium",
            title="Hidden",
            message="raw prompt should not be stored",
            source_type="generic",
            owner_scope=["workspace:main"],
        )

    with pytest.raises(ValidationError):
        NotificationRecord(
            notification_id="notification-2",
            topic_key="operator.action",
            status="delivered",
            severity="medium",
            title="Safe",
            message="Safe message.",
            source_type="generic",
            owner_scope=["workspace:main"],
            metadata={"api_key": "sk-test"},
        )


def test_escalation_and_digest_contracts_are_local_and_scoped() -> None:
    record = EscalationRecord(
        escalation_record_id="escalation-1",
        status="delivered_local",
        severity="high",
        escalation_channel="operator_inbox",
        escalation_target="operator",
        reason="matched",
        local_only=True,
    )
    digest = NotificationDigest(
        digest_id="digest-1",
        digest_type="operator",
        status="created",
        owner_scope=["workspace:main"],
        title="Digest",
        summary="One local item.",
    )

    assert record.local_only is True
    assert digest.owner_scope == ["workspace:main"]

    with pytest.raises(ValidationError):
        EscalationRecord(
            escalation_record_id="escalation-2",
            status="delivered_local",
            severity="high",
            escalation_channel="operator_inbox",
            escalation_target="operator",
            reason="matched",
            local_only=False,
        )


def test_alert_create_request_requires_scope() -> None:
    with pytest.raises(ValidationError):
        AlertCreateRequest(
            alert_type="generic",
            severity="high",
            title="Alert",
            description="Alert description.",
            source_type="generic",
            owner_scope=[],
        )
