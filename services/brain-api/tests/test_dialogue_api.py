from __future__ import annotations

from fastapi.testclient import TestClient

from aion_brain.kernel.app_factory import create_app
from tests.kernel_fakes import kernel_container


def test_dialogue_apis_work() -> None:
    client = TestClient(create_app(kernel_container()))

    session_response = client.post(
        "/brain/dialogue/sessions",
        json={"title": "API Session", "owner_scope": ["workspace:main"]},
    )
    assert session_response.status_code == 200
    session_id = session_response.json()["dialogue_session_id"]

    message_response = client.post(
        "/brain/dialogue/messages",
        json={"dialogue_session_id": session_id, "content": "hello"},
    )
    assert message_response.status_code == 200

    messages_response = client.get(
        f"/brain/dialogue/sessions/{session_id}/messages",
        params={"scope": "workspace:main"},
    )
    assert messages_response.status_code == 200
    assert len(messages_response.json()) == 1


def test_dialogue_turn_api_works() -> None:
    client = TestClient(create_app(kernel_container()))

    response = client.post(
        "/brain/dialogue/turn",
        json={"message": "hello", "owner_scope": ["workspace:main"], "mode": "assist"},
    )

    assert response.status_code == 200
    assert response.json()["response"]["response_id"]


def test_clarification_and_feedback_apis_work() -> None:
    client = TestClient(create_app(kernel_container()))
    turn = client.post(
        "/brain/dialogue/turn",
        json={"message": "hello", "owner_scope": ["workspace:main"], "mode": "assist"},
    ).json()

    pending = client.get(
        "/brain/dialogue/clarifications/pending",
        params={"scope": "workspace:main"},
    )
    assert pending.status_code == 200

    feedback = client.post(
        "/brain/dialogue/feedback",
        json={
            "feedback_id": "feedback-1",
            "dialogue_session_id": turn["dialogue_session"]["dialogue_session_id"],
            "response_id": turn["response"]["response_id"],
            "feedback_type": "helpful",
            "rating": 5,
            "metadata": {"owner_scope": ["workspace:main"]},
        },
    )
    assert feedback.status_code == 200
