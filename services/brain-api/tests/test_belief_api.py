from __future__ import annotations

from fastapi.testclient import TestClient

from aion_brain.kernel.app_factory import create_app
from tests.kernel_fakes import kernel_container


def test_belief_claim_api_create_get_query_and_revise() -> None:
    client = TestClient(create_app(kernel_container()))

    created = client.post(
        "/brain/beliefs/claims",
        json={
            "claim_text": "The belief API can create claims.",
            "source_type": "generic",
            "owner_scope": ["workspace:main"],
            "confidence": 0.7,
        },
    )
    assert created.status_code == 200
    claim_id = created.json()["claim_id"]

    fetched = client.get(
        f"/brain/beliefs/claims/{claim_id}",
        params={"scope": "workspace:main"},
    )
    queried = client.post(
        "/brain/beliefs/query",
        json={"query": "belief API", "scope": ["workspace:main"]},
    )
    revised = client.post(
        f"/brain/beliefs/claims/{claim_id}/revise",
        json={"to_status": "supported", "new_confidence": 0.9, "reason": "reviewed"},
    )

    assert fetched.status_code == 200
    assert queried.status_code == 200
    assert queried.json()["total_count"] == 1
    assert revised.status_code == 200
    assert revised.json()["to_status"] == "supported"


def test_belief_support_contradiction_extract_and_truth_api_work() -> None:
    client = TestClient(create_app(kernel_container()))
    claim = client.post(
        "/brain/beliefs/claims",
        json={
            "claim_text": "The belief API can collect supports.",
            "source_type": "generic",
            "owner_scope": ["workspace:main"],
        },
    ).json()

    support = client.post(
        "/brain/beliefs/supports",
        json={
            "claim_id": claim["claim_id"],
            "support_type": "evidence",
            "source_type": "evidence",
            "source_id": "evidence-1",
            "relation_type": "contradicts",
        },
    )
    contradictions = client.get(
        "/brain/beliefs/contradictions",
        params={"scope": "workspace:main"},
    )
    extract = client.post(
        "/brain/beliefs/extract",
        json={
            "source_type": "user_message",
            "source_id": "message-1",
            "text": "The extractor can create a generic claim.",
            "owner_scope": ["workspace:main"],
        },
    )
    truth = client.post(
        "/brain/beliefs/truth-maintenance/run",
        json={"owner_scope": ["workspace:main"], "claim_ids": [claim["claim_id"]]},
    )

    assert support.status_code == 200
    assert contradictions.status_code == 200
    assert contradictions.json()[0]["status"] == "open"
    assert extract.status_code == 200
    assert len(extract.json()["extracted_claims"]) == 1
    assert truth.status_code == 200
    assert truth.json()["status"] == "dry_run"
