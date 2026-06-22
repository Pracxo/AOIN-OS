from __future__ import annotations

from fastapi.testclient import TestClient

from aion_brain.kernel.app_factory import create_app
from tests.kernel_fakes import kernel_container


def test_explanation_api_endpoints_work() -> None:
    client = TestClient(create_app(kernel_container()))

    created = client.post(
        "/brain/explanations",
        json={
            "trace_id": "trace-1",
            "explanation_type": "generic",
            "target_type": "trace",
            "target_id": "trace-1",
            "owner_scope": ["workspace:main"],
            "metadata": {"evidence_refs": ["evidence-1"], "audit_refs": ["audit-1"]},
        },
    )
    assert created.status_code == 200
    explanation_id = created.json()["explanation_id"]

    fetched = client.get(
        f"/brain/explanations/{explanation_id}",
        params={"scope": "workspace:main"},
    )
    listed = client.get("/brain/explanations", params={"trace_id": "trace-1"})
    verified = client.post(f"/brain/explanations/{explanation_id}/verify")

    assert fetched.status_code == 200
    assert listed.status_code == 200
    assert verified.status_code == 200
    assert verified.json()["status"] == "passed"


def test_why_not_trace_narrative_and_feedback_api_endpoints_work() -> None:
    client = TestClient(create_app(kernel_container()))

    why_not = client.post(
        "/brain/explanations/why-not",
        json={
            "trace_id": "trace-1",
            "question": "Why did this not continue?",
            "target_type": "trace",
            "target_id": "trace-1",
            "owner_scope": ["workspace:main"],
            "metadata": {"approval_required": True},
        },
    )
    assert why_not.status_code == 200
    why_not_id = why_not.json()["why_not_id"]

    fetched_why_not = client.get(
        f"/brain/explanations/why-not/{why_not_id}",
        params={"scope": "workspace:main"},
    )
    narrative = client.post(
        "/brain/traces/trace-1/narrative",
        json={"trace_id": "trace-1", "owner_scope": ["workspace:main"]},
    )
    feedback = client.post(
        "/brain/explanations/feedback",
        json={
            "explanation_feedback_id": "feedback-1",
            "why_not_id": why_not_id,
            "feedback_type": "helpful",
            "rating": 5,
            "metadata": {"owner_scope": ["workspace:main"]},
        },
    )
    listed_feedback = client.get(
        "/brain/explanations/feedback",
        params={"why_not_id": why_not_id},
    )

    assert fetched_why_not.status_code == 200
    assert narrative.status_code == 200
    assert feedback.status_code == 200
    assert listed_feedback.status_code == 200
    assert listed_feedback.json()[0]["rating"] == 5
