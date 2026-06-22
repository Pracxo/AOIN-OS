from __future__ import annotations

from typing import Any

import httpx

from aion_sdk import AIONClient, AIONClientConfig


def _client(handler: Any) -> AIONClient:
    return AIONClient(
        AIONClientConfig(base_url="http://aion.test"),
        httpx.Client(transport=httpx.MockTransport(handler)),
    )


def test_backups_resource_export_calls_public_endpoint() -> None:
    seen: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["method"] = request.method
        seen["path"] = request.url.path
        return httpx.Response(200, json={"backup_job_id": "backup-1"})

    _client(handler).backups.export(
        {"owner_scope": ["workspace:main"], "resource_types": ["events"]}
    )

    assert seen == {"method": "POST", "path": "/brain/backups/export"}


def test_backups_resource_list_uses_scope_query() -> None:
    seen: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["path"] = request.url.path
        seen["scope"] = request.url.params.get("scope", "")
        return httpx.Response(200, json=[])

    _client(handler).backups.list(scope=["workspace:main"])

    assert seen["path"] == "/brain/backups"
    assert seen["scope"] == "workspace:main"


def test_backups_resource_restore_preview_and_apply_call_public_endpoints() -> None:
    seen: list[tuple[str, str]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append((request.method, request.url.path))
        return httpx.Response(200, json={"ok": True})

    client = _client(handler)
    client.backups.restore_preview({"backup_path": "artifacts/backups/backup-1"})
    client.backups.restore_apply({"restore_preview_id": "preview-1"})

    assert seen == [
        ("POST", "/brain/restore/preview"),
        ("POST", "/brain/restore/apply"),
    ]
