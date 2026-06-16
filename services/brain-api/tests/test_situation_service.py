from __future__ import annotations

import pytest

from aion_brain.contracts.situations import SituationCreateRequest, SituationQuery
from tests.situation_helpers import DenyPolicy, bundle


def test_situation_service_create_query_and_close() -> None:
    services = bundle()
    situation = services.situation_service.create(
        SituationCreateRequest(
            title="Current state",
            summary="Generic state.",
            owner_scope=["workspace:main"],
        )
    )

    result = services.situation_service.query(
        SituationQuery(scope=["workspace:main"], statuses=["active"], limit=10)
    )
    closed = services.situation_service.close(
        situation.situation_id,
        ["workspace:main"],
        reason="complete",
    )

    assert result.total == 1
    assert closed.status == "closed"
    assert any(
        getattr(event, "event_type", "") == "situation_closed"
        for event in services.telemetry.events
    )


def test_policy_deny_blocks_situation_create() -> None:
    services = bundle(DenyPolicy())

    with pytest.raises(PermissionError):
        services.situation_service.create(
            SituationCreateRequest(
                title="Current state",
                summary="Generic state.",
                owner_scope=["workspace:main"],
            )
        )
