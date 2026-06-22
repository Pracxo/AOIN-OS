from __future__ import annotations

from typing import Any

import httpx

from aion_sdk import AIONClient, AIONClientConfig


def _client(handler: Any) -> AIONClient:
    return AIONClient(
        AIONClientConfig(base_url="http://aion.test"),
        httpx.Client(transport=httpx.MockTransport(handler)),
    )


def test_registry_resource_calls_expected_endpoints() -> None:
    seen: list[tuple[str, str]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append((request.method, request.url.path))
        return httpx.Response(200, json={"ok": True})

    client = _client(handler)
    client.registry.upsert_resource({"descriptor": {}})
    client.registry.get_resource("generic", "res-1", ["workspace:main"])
    client.registry.get_by_uri("aion://generic/res-1", ["workspace:main"])
    client.registry.query({"scope": ["workspace:main"]})
    client.registry.create_link({"source_resource_uri": "aion://generic/a"}, ["workspace:main"])
    client.registry.list_links(["workspace:main"])
    client.registry.list_backlinks("aion://generic/res-1", ["workspace:main"])
    client.registry.validate({"owner_scope": ["workspace:main"]})
    client.registry.get_validation_run("validation-1", ["workspace:main"])
    client.registry.list_broken_references(["workspace:main"])
    client.registry.dismiss_broken_reference("broken-1", "dismissed", ["workspace:main"])
    client.registry.list_orphaned_resources(["workspace:main"])
    client.registry.dismiss_orphaned_resource("orphan-1", "dismissed", ["workspace:main"])
    client.registry.rebuild({"owner_scope": ["workspace:main"]})
    client.registry.get_rebuild_run("rebuild-1", ["workspace:main"])
    client.registry.create_snapshot({"scope": ["workspace:main"]})
    client.registry.get_snapshot("snapshot-1", ["workspace:main"])
    client.registry.list_snapshots(["workspace:main"])

    assert seen == [
        ("POST", "/brain/registry/resources"),
        ("GET", "/brain/registry/resources/generic/res-1"),
        ("GET", "/brain/registry/resources/by-uri"),
        ("POST", "/brain/registry/query"),
        ("POST", "/brain/registry/links"),
        ("GET", "/brain/registry/links"),
        ("GET", "/brain/registry/backlinks"),
        ("POST", "/brain/registry/validate"),
        ("GET", "/brain/registry/validation-runs/validation-1"),
        ("GET", "/brain/registry/broken-references"),
        ("POST", "/brain/registry/broken-references/broken-1/dismiss"),
        ("GET", "/brain/registry/orphaned-resources"),
        ("POST", "/brain/registry/orphaned-resources/orphan-1/dismiss"),
        ("POST", "/brain/registry/rebuild"),
        ("GET", "/brain/registry/rebuild-runs/rebuild-1"),
        ("POST", "/brain/registry/snapshots"),
        ("GET", "/brain/registry/snapshots/snapshot-1"),
        ("GET", "/brain/registry/snapshots"),
    ]


def test_registry_resource_does_not_import_brain_package() -> None:
    import aion_sdk.resources.registry as resource

    assert "aion_brain" not in resource.__dict__
