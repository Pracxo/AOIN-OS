from __future__ import annotations

from typing import Any

import httpx

from aion_sdk import AIONClient, AIONClientConfig


def _client(handler: Any) -> AIONClient:
    return AIONClient(
        AIONClientConfig(base_url="http://aion.test"),
        httpx.Client(transport=httpx.MockTransport(handler)),
    )


def test_contracts_resource_calls_expected_endpoints() -> None:
    seen: list[tuple[str, str]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append((request.method, request.url.path))
        return httpx.Response(200, json={"ok": True})

    client = _client(handler)
    client.contracts.list_contracts(["workspace:main"])
    client.contracts.list_interfaces(["workspace:main"])
    client.contracts.create_snapshot(["workspace:main"])
    client.contracts.get_snapshot("snapshot-1", ["workspace:main"])
    client.contracts.list_snapshots(["workspace:main"])
    client.contracts.create_rule({"compatibility_rule_id": "rule-1"})
    client.contracts.list_rules(["workspace:main"])
    client.contracts.seed_rules(["workspace:main"])
    client.contracts.scan_compatibility({"owner_scope": ["workspace:main"]})
    client.contracts.get_scan("scan-1")
    client.contracts.findings()
    client.contracts.dismiss_finding("finding-1", "dismiss")
    client.contracts.migration_notes(["workspace:main"])
    client.contracts.report(["workspace:main"])

    assert seen == [
        ("GET", "/brain/contracts/contracts"),
        ("GET", "/brain/contracts/interfaces"),
        ("POST", "/brain/contracts/snapshots"),
        ("GET", "/brain/contracts/snapshots/snapshot-1"),
        ("GET", "/brain/contracts/snapshots"),
        ("POST", "/brain/contracts/rules"),
        ("GET", "/brain/contracts/rules"),
        ("POST", "/brain/contracts/rules/seed-defaults"),
        ("POST", "/brain/contracts/compatibility/scan"),
        ("GET", "/brain/contracts/compatibility/scans/scan-1"),
        ("GET", "/brain/contracts/findings"),
        ("POST", "/brain/contracts/findings/finding-1/dismiss"),
        ("GET", "/brain/contracts/migration-notes"),
        ("POST", "/brain/contracts/report"),
    ]


def test_contracts_resource_does_not_import_brain_package() -> None:
    import aion_sdk.resources.contracts as resource

    assert "aion_brain" not in resource.__dict__
