from __future__ import annotations

from fastapi.testclient import TestClient

from aion_brain.kernel.app_factory import create_app
from tests.kernel_fakes import kernel_container


def test_outcome_api_endpoints_work() -> None:
    client = TestClient(create_app(kernel_container()))
    expected = client.post(
        "/brain/outcomes/expected-effects",
        json={
            "source_type": "command",
            "source_id": "command-1",
            "effect_type": "command_completed",
            "predicate": "status",
            "success_criteria": {"status_is": "completed"},
            "owner_scope": ["workspace:main"],
        },
    )
    assert expected.status_code == 200
    expected_id = expected.json()["expected_effect_id"]

    observed = client.post(
        "/brain/outcomes/observed-effects",
        json={
            "source_type": "command",
            "source_id": "command-1",
            "effect_type": "command_completed",
            "predicate": "status",
            "observed_value": {"status": "completed"},
            "observation_source_type": "command",
            "observation_source_id": "command-1",
            "owner_scope": ["workspace:main"],
        },
    )
    assert observed.status_code == 200
    observed_id = observed.json()["observed_effect_id"]

    outcome = client.post(
        "/brain/outcomes",
        json={
            "source_type": "command",
            "source_id": "command-1",
            "outcome_type": "command",
            "title": "Command outcome",
            "summary": "Expected effect matched.",
            "owner_scope": ["workspace:main"],
            "expected_effects": [expected_id],
            "observed_effects": [observed_id],
        },
    )
    assert outcome.status_code == 200
    outcome_id = outcome.json()["outcome_id"]

    assert (
        client.get(
            f"/brain/outcomes/{outcome_id}",
            params={"scope": "workspace:main"},
        ).status_code
        == 200
    )
    assert (
        client.post(
            "/brain/outcomes/query",
            json={"scope": ["workspace:main"], "source_types": ["command"]},
        ).status_code
        == 200
    )
    verification = client.post(
        "/brain/outcomes/verify",
        json={
            "outcome_id": outcome_id,
            "owner_scope": ["workspace:main"],
            "collect_observed_effects": False,
        },
    )
    assert verification.status_code == 200
    run_id = verification.json()["verification_run_id"]
    assert client.get(f"/brain/outcomes/verifications/{run_id}").status_code == 200
    assert client.get("/brain/outcomes/expected-effects").status_code == 200
    assert client.get("/brain/outcomes/observed-effects").status_code == 200
    assert (
        client.post(
            "/brain/outcomes/feedback",
            json={
                "outcome_feedback_id": "feedback-1",
                "outcome_id": outcome_id,
                "source_type": "outcome",
                "source_id": outcome_id,
                "feedback_type": "success_pattern",
                "status": "open",
                "severity": "low",
                "message": "Matched.",
                "recommended_followup": "Review only.",
                "metadata": {},
            },
        ).status_code
        == 200
    )
    assert client.get("/brain/outcomes/feedback").status_code == 200
    assert (
        client.post(
            f"/brain/outcomes/{outcome_id}/learning-bridge",
            json={"dry_run": True},
        ).status_code
        == 200
    )
