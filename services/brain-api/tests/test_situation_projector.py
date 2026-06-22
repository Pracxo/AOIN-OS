from __future__ import annotations

from aion_brain.contracts.situations import SituationProjectionRequest
from tests.situation_helpers import DenyPolicy, bundle


def test_projector_dry_run_does_not_persist() -> None:
    services = bundle()
    result = services.projector.project(
        SituationProjectionRequest(
            mode="dry_run",
            owner_scope=["workspace:main"],
            source_refs=[{"source_type": "event", "source_id": "event-1", "status": "active"}],
        )
    )

    assert result.status == "dry_run"
    assert result.state_atom_ids
    assert services.repository.get_projection_run(result.projection_run_id) is None


def test_projector_controlled_persists_projection_records() -> None:
    services = bundle()
    result = services.projector.project(
        SituationProjectionRequest(
            mode="controlled",
            owner_scope=["workspace:main"],
            source_refs=[{"source_type": "event", "source_id": "event-1", "status": "active"}],
        )
    )

    assert result.status == "completed"
    assert services.repository.get_projection_run(result.projection_run_id) is not None


def test_projector_policy_deny_returns_blocked_result() -> None:
    services = bundle(DenyPolicy())
    result = services.projector.project(
        SituationProjectionRequest(mode="dry_run", owner_scope=["workspace:main"])
    )

    assert result.status == "blocked_by_policy"
