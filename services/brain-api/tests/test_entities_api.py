from __future__ import annotations

from fastapi.testclient import TestClient

from aion_brain.kernel.app_factory import create_app
from tests.kernel_fakes import kernel_container


def test_entities_api_create_query_extract_resolve_and_references() -> None:
    client = TestClient(create_app(kernel_container()))

    created = client.post(
        "/brain/entities",
        json={
            "canonical_name": "Test Reference",
            "entity_type": "generic",
            "owner_scope": ["workspace:main"],
            "confidence": 0.8,
        },
    )
    assert created.status_code == 200
    entity_id = created.json()["entity_id"]

    query = client.post(
        "/brain/entities/query",
        json={"query": "test reference", "scope": ["workspace:main"]},
    )
    extracted = client.post(
        "/brain/entities/extract-mentions",
        json={
            "source_type": "dialogue_message",
            "source_id": "message-1",
            "text": "Use [[Test Reference]].",
            "owner_scope": ["workspace:main"],
        },
    )
    resolved = client.post(
        "/brain/entities/resolve",
        json={
            "source_type": "dialogue_message",
            "source_id": "message-1",
            "text": "Use [[Test Reference]].",
            "owner_scope": ["workspace:main"],
            "dry_run": False,
        },
    )
    link = client.post(
        "/brain/entities/references",
        params={"scope": "workspace:main"},
        json={
            "source_type": "memory",
            "source_id": "memory-1",
            "target_type": "entity",
            "target_id": entity_id,
            "entity_id": entity_id,
        },
    )
    links = client.get("/brain/entities/references", params={"scope": "workspace:main"})

    assert query.status_code == 200
    assert query.json()["entities"][0]["entity_id"] == entity_id
    assert extracted.status_code == 200
    assert extracted.json()[0]["mention_text"] == "Test Reference"
    assert resolved.status_code == 200
    assert resolved.json()["mentions_resolved"] == 1
    resolution_run = client.get(
        f"/brain/entities/resolution-runs/{resolved.json()['resolution_run_id']}",
        params={"scope": "workspace:main"},
    )
    mention = client.post(
        "/brain/entities/mentions",
        json={
            "entity_id": entity_id,
            "source_type": "memory",
            "source_id": "memory-1",
            "mention_text": "Test Reference",
            "owner_scope": ["workspace:main"],
        },
    )
    mentions = client.get(
        f"/brain/entities/{entity_id}/mentions",
        params={"scope": "workspace:main"},
    )
    assert link.status_code == 200
    assert links.status_code == 200
    assert links.json()[0]["target_id"] == entity_id
    assert resolution_run.status_code == 200
    assert resolution_run.json()["resolution_run_id"] == resolved.json()["resolution_run_id"]
    assert mention.status_code == 200
    assert mentions.status_code == 200
    assert any(item["mention_id"] == mention.json()["mention_id"] for item in mentions.json())


def test_entities_api_merge_split_and_delete_spec_paths() -> None:
    client = TestClient(create_app(kernel_container()))
    primary = client.post(
        "/brain/entities",
        json={
            "canonical_name": "Primary Reference",
            "owner_scope": ["workspace:main"],
            "confidence": 0.8,
        },
    ).json()
    duplicate = client.post(
        "/brain/entities",
        json={
            "canonical_name": "Primary Reference Duplicate",
            "owner_scope": ["workspace:main"],
            "confidence": 0.7,
        },
    ).json()

    merge = client.post(
        "/brain/entities/merge-proposals",
        params={"scope": "workspace:main"},
        json={
            "primary_entity_id": primary["entity_id"],
            "duplicate_entity_id": duplicate["entity_id"],
            "reason": "same generic reference",
        },
    )
    approved = client.post(
        f"/brain/entities/merge-proposals/{merge.json()['merge_proposal_id']}/approve",
        params={"scope": "workspace:main"},
        json={"reason": "approved", "approval_present": True},
    )
    split = client.post(
        "/brain/entities/split-proposals",
        params={"scope": "workspace:main"},
        json={"entity_id": primary["entity_id"], "reason": "too broad"},
    )
    rejected = client.post(
        f"/brain/entities/split-proposals/{split.json()['split_proposal_id']}/reject",
        params={"scope": "workspace:main"},
        json={"reason": "not needed", "approval_present": True},
    )
    deleted = client.request(
        "DELETE",
        f"/brain/entities/{duplicate['entity_id']}",
        params={"scope": "workspace:main"},
        json={"reason": "cleanup"},
    )

    assert merge.status_code == 200
    assert approved.status_code == 200
    assert approved.json()["status"] == "completed"
    assert split.status_code == 200
    assert rejected.status_code == 200
    assert rejected.json()["status"] == "rejected"
    assert deleted.status_code == 200
    assert deleted.json() == {"deleted": True, "entity_id": duplicate["entity_id"]}
