"""Notification and alert API."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field

from aion_brain.api.kernel import get_kernel_container
from aion_brain.api_support.errors import AIONPolicyDeniedException
from aion_brain.contracts.alerts import AlertCreateRequest, AlertQuery, AlertRecord
from aion_brain.contracts.notifications import (
    EscalationPolicy,
    EscalationRecord,
    NotificationDigest,
    NotificationPublishRequest,
    NotificationQuery,
    NotificationRecord,
    NotificationSubscription,
    NotificationTopic,
)
from aion_brain.contracts.scopes import ActorContext
from aion_brain.identity.dev_auth import get_actor_context
from aion_brain.kernel.container import KernelContainer

router = APIRouter(tags=["notifications"])


class SeedTopicsBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scope: list[str] | None = None
    dry_run: bool = True


class ReasonBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    actor_id: str | None = None
    reason: str = Field(min_length=1)


class EscalationEvaluateBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    alert_id: str | None = None
    notification_id: str | None = None
    scope: list[str] | None = None


class DigestCreateBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scope: list[str] | None = None
    digest_type: str = "operator"
    actor_id: str | None = None
    workspace_id: str | None = None
    created_by: str | None = None


@router.post("/brain/notifications/topics", response_model=NotificationTopic)
def create_topic(
    body: NotificationTopic,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> NotificationTopic:
    try:
        return container.notification_topic_service.with_actor_context(actor_context).create_topic(
            body
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.get("/brain/notifications/topics", response_model=list[NotificationTopic])
def list_topics(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
    status: str | None = None,
    category: str | None = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> list[NotificationTopic]:
    try:
        return container.notification_topic_service.with_actor_context(actor_context).list_topics(
            _scope(scope, actor_context), status=status, category=category, limit=limit
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.post("/brain/notifications/topics/seed-defaults", response_model=dict[str, object])
def seed_topics(
    body: SeedTopicsBody,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> dict[str, object]:
    try:
        return container.notification_topic_service.with_actor_context(
            actor_context
        ).seed_default_topics(_scope(body.scope, actor_context), dry_run=body.dry_run)
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.post("/brain/notifications/subscriptions", response_model=NotificationSubscription)
def create_subscription(
    body: NotificationSubscription,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> NotificationSubscription:
    try:
        return container.notification_subscription_service.with_actor_context(
            actor_context
        ).create_subscription(body)
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.get("/brain/notifications/subscriptions", response_model=list[NotificationSubscription])
def list_subscriptions(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
    topic_key: str | None = None,
    actor_id: str | None = None,
    workspace_id: str | None = None,
    status: str | None = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> list[NotificationSubscription]:
    try:
        return container.notification_subscription_service.with_actor_context(
            actor_context
        ).list_subscriptions(
            _scope(scope, actor_context),
            topic_key=topic_key,
            actor_id=actor_id,
            workspace_id=workspace_id,
            status=status,
            limit=limit,
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.post("/brain/notifications/publish", response_model=NotificationRecord)
def publish_notification(
    body: NotificationPublishRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> NotificationRecord:
    try:
        return container.notification_router.with_actor_context(actor_context).publish(
            _publish_with_context(body, actor_context)
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.post("/brain/notifications/query", response_model=list[NotificationRecord])
def query_notifications(
    body: NotificationQuery,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> list[NotificationRecord]:
    try:
        return container.notification_query_service.with_actor_context(actor_context).query(body)
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.post("/brain/alerts", response_model=AlertRecord)
def create_alert(
    body: AlertCreateRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> AlertRecord:
    try:
        return container.alert_service.with_actor_context(actor_context).create_alert(
            _alert_with_context(body, actor_context)
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.post("/brain/alerts/query", response_model=list[AlertRecord])
def query_alerts(
    body: AlertQuery,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> list[AlertRecord]:
    try:
        return container.alert_service.with_actor_context(actor_context).query(body)
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.post("/brain/escalations/policies", response_model=EscalationPolicy)
def create_escalation_policy(
    body: EscalationPolicy,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> EscalationPolicy:
    try:
        return container.escalation_service.with_actor_context(actor_context).create_policy(body)
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.get("/brain/escalations/policies", response_model=list[EscalationPolicy])
def list_escalation_policies(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
    status: str | None = None,
    topic_key: str | None = None,
    alert_type: str | None = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> list[EscalationPolicy]:
    try:
        return container.escalation_service.with_actor_context(actor_context).list_policies(
            _scope(scope, actor_context),
            status=status,
            topic_key=topic_key,
            alert_type=alert_type,
            limit=limit,
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.post("/brain/escalations/evaluate", response_model=list[EscalationRecord])
def evaluate_escalations(
    body: EscalationEvaluateBody,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> list[EscalationRecord]:
    try:
        return container.escalation_service.with_actor_context(actor_context).evaluate(
            alert_id=body.alert_id,
            notification_id=body.notification_id,
            scope=_scope(body.scope, actor_context),
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.get("/brain/escalations", response_model=list[EscalationRecord])
def list_escalations(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
    status: str | None = None,
    severity: str | None = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> list[EscalationRecord]:
    try:
        return container.escalation_service.with_actor_context(actor_context).list_records(
            _scope(scope, actor_context), status=status, severity=severity, limit=limit
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.post("/brain/notifications/digests", response_model=NotificationDigest)
def create_digest(
    body: DigestCreateBody,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> NotificationDigest:
    try:
        return container.notification_digest_service.with_actor_context(
            actor_context
        ).create_digest(
            _scope(body.scope, actor_context),
            body.digest_type,
            actor_id=body.actor_id,
            workspace_id=body.workspace_id,
            created_by=body.created_by,
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.get("/brain/notifications/digests", response_model=list[NotificationDigest])
def list_digests(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
    digest_type: str | None = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 50,
) -> list[NotificationDigest]:
    try:
        return container.notification_digest_service.with_actor_context(actor_context).list_digests(
            _scope(scope, actor_context), digest_type=digest_type, limit=limit
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.post("/brain/notifications/{notification_id}/read", response_model=NotificationRecord)
def mark_notification_read(
    notification_id: str,
    body: ReasonBody,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> NotificationRecord:
    return _notification_update(container, actor_context, notification_id, body, "read")


@router.post(
    "/brain/notifications/{notification_id}/acknowledge",
    response_model=NotificationRecord,
)
def acknowledge_notification(
    notification_id: str,
    body: ReasonBody,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> NotificationRecord:
    return _notification_update(container, actor_context, notification_id, body, "acknowledge")


@router.post("/brain/notifications/{notification_id}/resolve", response_model=NotificationRecord)
def resolve_notification(
    notification_id: str,
    body: ReasonBody,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> NotificationRecord:
    return _notification_update(container, actor_context, notification_id, body, "resolve")


@router.post("/brain/alerts/{alert_id}/acknowledge", response_model=AlertRecord)
def acknowledge_alert(
    alert_id: str,
    body: ReasonBody,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> AlertRecord:
    return _alert_update(container, actor_context, alert_id, body, "acknowledge")


@router.post("/brain/alerts/{alert_id}/resolve", response_model=AlertRecord)
def resolve_alert(
    alert_id: str,
    body: ReasonBody,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> AlertRecord:
    return _alert_update(container, actor_context, alert_id, body, "resolve")


def _notification_update(
    container: KernelContainer,
    actor_context: ActorContext,
    notification_id: str,
    body: ReasonBody,
    action: str,
) -> NotificationRecord:
    try:
        router = container.notification_router.with_actor_context(actor_context)
        if action == "read":
            return router.mark_read(notification_id, body.actor_id, body.reason)
        if action == "acknowledge":
            return router.acknowledge(notification_id, body.actor_id, body.reason)
        return router.resolve(notification_id, body.actor_id, body.reason)
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


def _alert_update(
    container: KernelContainer,
    actor_context: ActorContext,
    alert_id: str,
    body: ReasonBody,
    action: str,
) -> AlertRecord:
    try:
        service = container.alert_service.with_actor_context(actor_context)
        if action == "acknowledge":
            return service.acknowledge(alert_id, body.actor_id, body.reason)
        return service.resolve(alert_id, body.actor_id, body.reason)
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


def _scope(scope: list[str] | None, actor_context: ActorContext) -> list[str]:
    return scope or actor_context.security_scope or ["workspace:main"]


def _publish_with_context(
    request: NotificationPublishRequest, actor_context: ActorContext
) -> NotificationPublishRequest:
    return request.model_copy(
        update={
            "actor_id": request.actor_id or actor_context.actor_id,
            "workspace_id": request.workspace_id or actor_context.workspace_id,
            "created_by": request.created_by or actor_context.actor_id,
        }
    )


def _alert_with_context(
    request: AlertCreateRequest, actor_context: ActorContext
) -> AlertCreateRequest:
    return request.model_copy(
        update={
            "actor_id": request.actor_id or actor_context.actor_id,
            "workspace_id": request.workspace_id or actor_context.workspace_id,
            "created_by": request.created_by or actor_context.actor_id,
        }
    )


__all__ = ["router"]
