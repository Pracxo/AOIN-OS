from __future__ import annotations

from fastapi.testclient import TestClient

from aion_brain.kernel.app_factory import create_app
from tests.kernel_fakes import kernel_container


def test_instruction_preference_and_style_api_endpoints_work() -> None:
    client = TestClient(create_app(kernel_container()))

    instruction = client.post(
        "/brain/instructions",
        json={
            "instruction_text": "Keep responses concise.",
            "instruction_type": "response_style",
            "source_type": "user",
            "scope_type": "actor",
            "owner_scope": ["workspace:main"],
            "priority": 500,
        },
    )
    assert instruction.status_code == 200
    instruction_id = instruction.json()["instruction_id"]

    listed = client.get("/brain/instructions", params={"scope": "workspace:main"})
    resolved = client.post(
        "/brain/instructions/resolve",
        json={"owner_scope": ["workspace:main"]},
    )
    disabled = client.post(
        f"/brain/instructions/{instruction_id}/disable",
        json={"reason": "test"},
    )

    assert listed.status_code == 200
    assert resolved.status_code == 200
    assert disabled.status_code == 200
    assert disabled.json()["status"] == "disabled"

    preference = client.post(
        "/brain/preferences",
        json={
            "preference_key": "style.verbosity",
            "preference_type": "response_style",
            "preference_value": {"value": "concise"},
            "status": "candidate",
            "confidence": 0.7,
            "owner_scope": ["workspace:main"],
        },
    )
    assert preference.status_code == 200
    preference_id = preference.json()["preference_id"]

    preferences = client.get("/brain/preferences", params={"scope": "workspace:main"})
    confirmed = client.post(
        f"/brain/preferences/{preference_id}/confirm",
        json={"reason": "explicit"},
    )

    assert preferences.status_code == 200
    assert confirmed.status_code == 200
    assert confirmed.json()["status"] == "confirmed"

    style = client.post(
        "/brain/style-profiles",
        json={
            "name": "Direct",
            "description": "Direct style.",
            "owner_scope": ["workspace:main"],
            "style_rules": {"tone": "direct"},
        },
    )
    effective = client.get(
        "/brain/style-profiles/effective",
        params={"scope": "workspace:main"},
    )

    assert style.status_code == 200
    assert effective.status_code == 200
    assert effective.json()["name"] == "Direct"


def test_constraints_and_candidate_api_endpoints_work() -> None:
    client = TestClient(create_app(kernel_container()))

    constraint = client.post(
        "/brain/constraints",
        json={
            "constraint_id": "constraint-1",
            "constraint_key": "policy.mode",
            "constraint_type": "policy",
            "status": "active",
            "severity": "high",
            "description": "Policy-owned constraint.",
            "rule": {"value": "bounded"},
            "source_type": "policy",
            "owner_scope": ["workspace:main"],
        },
    )
    listed_constraints = client.get("/brain/constraints", params={"scope": "workspace:main"})

    candidate = client.post(
        "/brain/preferences/candidates",
        json={
            "candidate_id": "candidate-1",
            "preference_key": "style.structure",
            "preference_type": "response_style",
            "proposed_value": {"value": "structured"},
            "status": "proposed",
            "confidence": 0.6,
            "reason": "Explicit request.",
            "source_type": "dialogue",
            "owner_scope": ["workspace:main"],
        },
    )
    candidates = client.get(
        "/brain/preferences/candidates",
        params={"scope": "workspace:main"},
    )
    confirmed_candidate = client.post(
        "/brain/preferences/candidates/candidate-1/confirm",
        json={"reason": "explicit"},
    )

    assert constraint.status_code == 200
    assert listed_constraints.status_code == 200
    assert candidate.status_code == 200
    assert candidates.status_code == 200
    assert confirmed_candidate.status_code == 200
    assert confirmed_candidate.json()["status"] == "confirmed"
