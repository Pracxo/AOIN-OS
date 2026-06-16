from __future__ import annotations

from datetime import timedelta

from aion_brain.contracts.temporal_state import TemporalStateWindowRequest
from tests.situation_helpers import bundle, now


def test_temporal_window_service_create_get_and_list() -> None:
    services = bundle()
    end_at = now()
    window = services.temporal_window_service.create(
        TemporalStateWindowRequest(
            owner_scope=["workspace:main"],
            start_at=end_at - timedelta(hours=1),
            end_at=end_at,
            state_atom_ids=["atom-1"],
        )
    )

    retrieved = services.temporal_window_service.get(
        window.temporal_window_id,
        ["workspace:main"],
    )
    listed = services.temporal_window_service.list_windows(scope=["workspace:main"])
    assert retrieved is not None
    assert listed[0].temporal_window_id == window.temporal_window_id
