from __future__ import annotations

from typing import Any

import httpx

from aion_sdk import AIONClient, AIONClientConfig


def _client(handler: Any) -> AIONClient:
    return AIONClient(
        AIONClientConfig(base_url="http://aion.test"),
        httpx.Client(transport=httpx.MockTransport(handler)),
    )


def test_concepts_and_entities_resources_call_expected_endpoints() -> None:
    seen: list[tuple[str, str]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append((request.method, request.url.path))
        return httpx.Response(200, json={"ok": True})

    client = _client(handler)
    client.concepts.create({"name": "Concept", "owner_scope": ["workspace:main"]})
    client.entities.create({"canonical_name": "Entity", "owner_scope": ["workspace:main"]})
    client.entities.resolve({"owner_scope": ["workspace:main"], "text": "Entity"})
    client.entities.get_resolution_run("resolution-1", ["workspace:main"])
    client.entities.delete("entity-1", "cleanup", ["workspace:main"])
    client.entities.propose_merge(
        {"primary_entity_id": "entity-1", "duplicate_entity_id": "entity-2", "reason": "same"},
        ["workspace:main"],
    )
    client.entities.propose_split(
        {"entity_id": "entity-1", "reason": "too broad"},
        ["workspace:main"],
    )

    assert seen == [
        ("POST", "/brain/concepts"),
        ("POST", "/brain/entities"),
        ("POST", "/brain/entities/resolve"),
        ("GET", "/brain/entities/resolution-runs/resolution-1"),
        ("DELETE", "/brain/entities/entity-1"),
        ("POST", "/brain/entities/merge-proposals"),
        ("POST", "/brain/entities/split-proposals"),
    ]


def test_resources_do_not_import_brain_package() -> None:
    import aion_sdk.resources.concepts as concepts_resource
    import aion_sdk.resources.entities as entities_resource

    assert "aion_brain" not in concepts_resource.__dict__
    assert "aion_brain" not in entities_resource.__dict__
