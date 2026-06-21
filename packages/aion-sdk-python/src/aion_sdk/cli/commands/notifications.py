"""aionctl notification center commands."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated, Any, cast

import typer

from aion_sdk.client import AIONClient
from aion_sdk.types import JSONDict

notifications_app = typer.Typer(no_args_is_help=True, help="Notification center commands.")
topics_app = typer.Typer(no_args_is_help=True, help="Notification topic commands.")
subscriptions_app = typer.Typer(no_args_is_help=True, help="Notification subscription commands.")
alerts_app = typer.Typer(no_args_is_help=True, help="Alert commands.")
escalations_app = typer.Typer(no_args_is_help=True, help="Escalation commands.")
digests_app = typer.Typer(no_args_is_help=True, help="Notification digest commands.")


def install_notification_commands(
    app: typer.Typer,
    *,
    get_client: Any,
    get_scope: Any,
    render: Any,
) -> None:
    """Install notification center commands."""

    app.add_typer(notifications_app, name="notifications")
    notifications_app.add_typer(topics_app, name="topics")
    notifications_app.add_typer(subscriptions_app, name="subscriptions")
    notifications_app.add_typer(alerts_app, name="alerts")
    notifications_app.add_typer(escalations_app, name="escalations")
    notifications_app.add_typer(digests_app, name="digests")

    @topics_app.command("create")
    def create_topic(
        ctx: typer.Context,
        payload_file: Annotated[Path, typer.Option("--payload-file")],
    ) -> None:
        payload = _load_payload(payload_file)
        payload.setdefault("owner_scope", get_scope(ctx))
        render(ctx, _client(get_client(ctx)).notifications.create_topic(payload))

    @topics_app.command("list")
    def list_topics(
        ctx: typer.Context,
        status: Annotated[str | None, typer.Option("--status")] = None,
        category: Annotated[str | None, typer.Option("--category")] = None,
        limit: Annotated[int, typer.Option("--limit")] = 100,
    ) -> None:
        render(
            ctx,
            _client(get_client(ctx)).notifications.list_topics(
                get_scope(ctx),
                status=status,
                category=category,
                limit=limit,
            ),
        )

    @topics_app.command("seed-defaults")
    def seed_topics(
        ctx: typer.Context,
        dry_run: Annotated[
            bool,
            typer.Option("--dry-run/--apply", help="Preview by default; --apply persists."),
        ] = True,
    ) -> None:
        render(
            ctx,
            _client(get_client(ctx)).notifications.seed_default_topics(
                get_scope(ctx),
                dry_run=dry_run,
            ),
        )

    @subscriptions_app.command("create")
    def create_subscription(
        ctx: typer.Context,
        payload_file: Annotated[Path, typer.Option("--payload-file")],
    ) -> None:
        payload = _load_payload(payload_file)
        payload.setdefault("owner_scope", get_scope(ctx))
        render(ctx, _client(get_client(ctx)).notifications.create_subscription(payload))

    @subscriptions_app.command("list")
    def list_subscriptions(
        ctx: typer.Context,
        topic_key: Annotated[str | None, typer.Option("--topic-key")] = None,
        status: Annotated[str | None, typer.Option("--status")] = None,
        limit: Annotated[int, typer.Option("--limit")] = 100,
    ) -> None:
        render(
            ctx,
            _client(get_client(ctx)).notifications.list_subscriptions(
                get_scope(ctx),
                topic_key=topic_key,
                status=status,
                limit=limit,
            ),
        )

    @notifications_app.command("publish")
    def publish(
        ctx: typer.Context,
        payload_file: Annotated[Path | None, typer.Option("--payload-file")] = None,
        topic_key: Annotated[str | None, typer.Option("--topic-key")] = None,
        title: Annotated[str | None, typer.Option("--title")] = None,
        message: Annotated[str | None, typer.Option("--message")] = None,
        severity: Annotated[str | None, typer.Option("--severity")] = None,
        source_type: Annotated[str, typer.Option("--source-type")] = "generic",
    ) -> None:
        payload = _load_payload(payload_file)
        payload.setdefault("owner_scope", get_scope(ctx))
        payload.setdefault("source_type", source_type)
        if topic_key is not None:
            payload["topic_key"] = topic_key
        if title is not None:
            payload["title"] = title
        if message is not None:
            payload["message"] = message
        if severity is not None:
            payload["severity"] = severity
        render(ctx, _client(get_client(ctx)).notifications.publish(payload))

    @notifications_app.command("query")
    def query(
        ctx: typer.Context,
        payload_file: Annotated[Path | None, typer.Option("--payload-file")] = None,
        status: Annotated[str | None, typer.Option("--status")] = None,
        severity: Annotated[str | None, typer.Option("--severity")] = None,
        topic_key: Annotated[str | None, typer.Option("--topic-key")] = None,
        limit: Annotated[int, typer.Option("--limit")] = 50,
    ) -> None:
        payload = _load_payload(payload_file)
        payload.setdefault("scope", get_scope(ctx))
        payload.setdefault("limit", limit)
        if status is not None:
            payload["status"] = status
        if severity is not None:
            payload["severity"] = severity
        if topic_key is not None:
            payload["topic_key"] = topic_key
        render(ctx, _client(get_client(ctx)).notifications.query(payload))

    @notifications_app.command("acknowledge")
    def acknowledge(
        ctx: typer.Context,
        notification_id: Annotated[str, typer.Option("--notification-id")],
        reason: Annotated[str, typer.Option("--reason")] = "operator_acknowledged",
    ) -> None:
        render(
            ctx,
            _client(get_client(ctx)).notifications.acknowledge(notification_id, reason),
        )

    @alerts_app.command("create")
    def create_alert(
        ctx: typer.Context,
        payload_file: Annotated[Path, typer.Option("--payload-file")],
    ) -> None:
        payload = _load_payload(payload_file)
        payload.setdefault("owner_scope", get_scope(ctx))
        render(ctx, _client(get_client(ctx)).notifications.create_alert(payload))

    @alerts_app.command("query")
    def query_alerts(
        ctx: typer.Context,
        payload_file: Annotated[Path | None, typer.Option("--payload-file")] = None,
        status: Annotated[str | None, typer.Option("--status")] = None,
        severity: Annotated[str | None, typer.Option("--severity")] = None,
        limit: Annotated[int, typer.Option("--limit")] = 50,
    ) -> None:
        payload = _load_payload(payload_file)
        payload.setdefault("scope", get_scope(ctx))
        payload.setdefault("limit", limit)
        if status is not None:
            payload["status"] = status
        if severity is not None:
            payload["severity"] = severity
        render(ctx, _client(get_client(ctx)).notifications.query_alerts(payload))

    @alerts_app.command("acknowledge")
    def acknowledge_alert(
        ctx: typer.Context,
        alert_id: Annotated[str, typer.Option("--alert-id")],
        reason: Annotated[str, typer.Option("--reason")] = "operator_acknowledged",
    ) -> None:
        render(ctx, _client(get_client(ctx)).notifications.acknowledge_alert(alert_id, reason))

    @alerts_app.command("resolve")
    def resolve_alert(
        ctx: typer.Context,
        alert_id: Annotated[str, typer.Option("--alert-id")],
        reason: Annotated[str, typer.Option("--reason")] = "operator_resolved",
    ) -> None:
        render(ctx, _client(get_client(ctx)).notifications.resolve_alert(alert_id, reason))

    @escalations_app.command("policies")
    def list_escalation_policies(
        ctx: typer.Context,
        status: Annotated[str | None, typer.Option("--status")] = None,
        limit: Annotated[int, typer.Option("--limit")] = 100,
    ) -> None:
        render(
            ctx,
            _client(get_client(ctx)).notifications.list_escalation_policies(
                get_scope(ctx),
                status=status,
                limit=limit,
            ),
        )

    @escalations_app.command("policy-create")
    def create_escalation_policy(
        ctx: typer.Context,
        payload_file: Annotated[Path, typer.Option("--payload-file")],
    ) -> None:
        payload = _load_payload(payload_file)
        payload.setdefault("owner_scope", get_scope(ctx))
        render(ctx, _client(get_client(ctx)).notifications.create_escalation_policy(payload))

    @escalations_app.command("evaluate")
    def evaluate_escalations(
        ctx: typer.Context,
        alert_id: Annotated[str | None, typer.Option("--alert-id")] = None,
        notification_id: Annotated[str | None, typer.Option("--notification-id")] = None,
    ) -> None:
        render(
            ctx,
            _client(get_client(ctx)).notifications.evaluate_escalations(
                get_scope(ctx),
                alert_id=alert_id,
                notification_id=notification_id,
            ),
        )

    @escalations_app.command("list")
    def list_escalations(
        ctx: typer.Context,
        status: Annotated[str | None, typer.Option("--status")] = None,
        severity: Annotated[str | None, typer.Option("--severity")] = None,
        limit: Annotated[int, typer.Option("--limit")] = 100,
    ) -> None:
        render(
            ctx,
            _client(get_client(ctx)).notifications.list_escalations(
                get_scope(ctx),
                status=status,
                severity=severity,
                limit=limit,
            ),
        )

    @digests_app.command("create")
    def create_digest(
        ctx: typer.Context,
        digest_type: Annotated[str, typer.Option("--digest-type")] = "operator",
    ) -> None:
        render(
            ctx,
            _client(get_client(ctx)).notifications.create_digest(
                get_scope(ctx),
                digest_type=digest_type,
            ),
        )

    @digests_app.command("list")
    def list_digests(
        ctx: typer.Context,
        digest_type: Annotated[str | None, typer.Option("--digest-type")] = None,
        limit: Annotated[int, typer.Option("--limit")] = 50,
    ) -> None:
        render(
            ctx,
            _client(get_client(ctx)).notifications.list_digests(
                get_scope(ctx),
                digest_type=digest_type,
                limit=limit,
            ),
        )


def _load_payload(path: Path | None) -> JSONDict:
    if path is None:
        return {}
    loaded = json.loads(path.read_text())
    if not isinstance(loaded, dict):
        raise typer.BadParameter("payload file must contain a JSON object")
    return cast(JSONDict, loaded)


def _client(value: object) -> AIONClient:
    return cast(AIONClient, value)


__all__ = ["install_notification_commands"]
