from __future__ import annotations

import json
from typing import Any

from typer.testing import CliRunner

from aion_sdk.cli import main as cli_main
from aion_sdk.config import AIONClientConfig

runner = CliRunner()


class FakeNotifications:
    def publish(self, payload: dict[str, Any]) -> dict[str, object]:
        return {"notification": payload}

    def query(self, payload: dict[str, Any]) -> dict[str, object]:
        return {"query": payload}

    def query_alerts(self, payload: dict[str, Any]) -> dict[str, object]:
        return {"alerts": [], "query": payload}

    def create_digest(
        self, scope: list[str], *, digest_type: str = "operator"
    ) -> dict[str, object]:
        return {"scope": scope, "digest_type": digest_type}


class FakeClient:
    def __init__(self, config: AIONClientConfig) -> None:
        self.config = config
        self.notifications = FakeNotifications()


def test_cli_notifications_publish(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(cli_main, "make_client", lambda config: FakeClient(config))

    result = runner.invoke(
        cli_main.app,
        [
            "--json",
            "notifications",
            "publish",
            "--topic-key",
            "generic.info",
            "--title",
            "Local",
            "--message",
            "Local only.",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)["notification"]
    assert payload["topic_key"] == "generic.info"
    assert payload["owner_scope"] == ["workspace:main"]


def test_cli_notifications_alert_query(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(cli_main, "make_client", lambda config: FakeClient(config))

    result = runner.invoke(
        cli_main.app,
        [
            "--json",
            "notifications",
            "alerts",
            "query",
            "--status",
            "open",
            "--severity",
            "critical",
        ],
    )

    assert result.exit_code == 0
    query = json.loads(result.stdout)["query"]
    assert query["status"] == "open"
    assert query["severity"] == "critical"


def test_cli_notifications_digest_create(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(cli_main, "make_client", lambda config: FakeClient(config))

    result = runner.invoke(
        cli_main.app,
        ["--json", "notifications", "digests", "create", "--digest-type", "operator"],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["digest_type"] == "operator"
