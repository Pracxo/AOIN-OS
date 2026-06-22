from __future__ import annotations

from fastapi.testclient import TestClient

from aion_brain.kernel.app_factory import create_app
from tests.kernel_fakes import kernel_container


def test_grounding_api_endpoints_work() -> None:
    client = TestClient(create_app(kernel_container()))

    source = client.post(
        "/brain/grounding/sources",
        json={
            "source_type": "evidence",
            "source_id": "evidence-1",
            "title": "Evidence",
            "summary": "AION records deterministic source support.",
            "trust_level": "primary",
            "evidence_refs": ["evidence-1"],
            "owner_scope": ["workspace:main"],
        },
    )
    assert source.status_code == 200

    mapped = client.post(
        "/brain/grounding/map-text",
        json={
            "text": "AION records deterministic source support.",
            "trace_id": "trace-1",
            "owner_scope": ["workspace:main"],
            "sources": [source.json()],
            "target_type": "response",
            "target_id": "response-1",
        },
    )
    verified = client.post(
        "/brain/grounding/verify",
        json={
            "trace_id": "trace-1",
            "response_id": "response-1",
            "target_type": "response",
            "target_id": "response-1",
            "owner_scope": ["workspace:main"],
            "text": "AION records deterministic source support.",
        },
    )
    query = client.post(
        "/brain/grounding/query",
        json={"scope": ["workspace:main"], "response_id": "response-1"},
    )

    assert mapped.status_code == 200
    assert mapped.json()["citation_ids"]
    assert verified.status_code == 200
    assert query.status_code == 200
