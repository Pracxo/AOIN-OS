from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient

from aion_brain.kernel.app_factory import create_app
from tests.kernel_fakes import kernel_container


def test_situation_api_endpoints_work() -> None:
    client = TestClient(create_app(kernel_container()))
    created = client.post(
        "/brain/situations",
        json={
            "title": "Current state",
            "summary": "Generic API state.",
            "owner_scope": ["workspace:main"],
        },
    )
    assert created.status_code == 200
    situation_id = created.json()["situation_id"]

    retrieved = client.get(
        f"/brain/situations/{situation_id}",
        params={"scope": "workspace:main"},
    )
    queried = client.post(
        "/brain/situations/query",
        json={"scope": ["workspace:main"], "limit": 10},
    )
    closed = client.post(
        f"/brain/situations/{situation_id}/close",
        json={"reason": "done"},
        params={"scope": "workspace:main"},
    )
    assert retrieved.status_code == 200
    assert queried.status_code == 200
    assert closed.status_code == 200


def test_situation_state_projection_temporal_and_continuity_api() -> None:
    client = TestClient(create_app(kernel_container()))
    atom = client.post(
        "/brain/situations/state-atoms",
        json={
            "source_id": "source-1",
            "predicate": "status",
            "value": {"status": "active"},
            "owner_scope": ["workspace:main"],
        },
    )
    assert atom.status_code == 200
    atom_id = atom.json()["state_atom_id"]
    fetched_atom = client.get(
        f"/brain/situations/state-atoms/{atom_id}",
        params={"scope": "workspace:main"},
    )
    listed_atoms = client.get(
        "/brain/situations/state-atoms",
        params={"scope": "workspace:main"},
    )
    assert fetched_atom.status_code == 200
    assert listed_atoms.status_code == 200

    projection = client.post(
        "/brain/situations/project",
        json={
            "mode": "dry_run",
            "owner_scope": ["workspace:main"],
            "source_refs": [{"source_type": "event", "source_id": "event-1"}],
        },
    )
    assert projection.status_code == 200
    assert client.get("/brain/situations/transitions").status_code == 200

    end_at = datetime.now(UTC)
    window = client.post(
        "/brain/situations/temporal-windows",
        json={
            "owner_scope": ["workspace:main"],
            "start_at": (end_at - timedelta(hours=1)).isoformat(),
            "end_at": end_at.isoformat(),
            "state_atom_ids": [atom_id],
        },
    )
    assert window.status_code == 200
    window_id = window.json()["temporal_window_id"]
    fetched_window = client.get(
        f"/brain/situations/temporal-windows/{window_id}",
        params={"scope": "workspace:main"},
    )
    listed_windows = client.get(
        "/brain/situations/temporal-windows",
        params={"scope": "workspace:main"},
    )
    assert fetched_window.status_code == 200
    assert listed_windows.status_code == 200

    continuity = client.post(
        "/brain/situations/continuity",
        json={"owner_scope": ["workspace:main"], "refs": ["goal-1"]},
    )
    assert continuity.status_code == 200
    listed_continuity = client.get(
        "/brain/situations/continuity",
        params={"scope": "workspace:main"},
    )
    assert listed_continuity.status_code == 200
