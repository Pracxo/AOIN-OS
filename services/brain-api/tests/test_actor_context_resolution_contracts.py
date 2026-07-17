"""AION-160 actor-context resolution contract tests."""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from aion_brain.contracts.actor_context_resolution import (
    REQUIRED_REASON_CODES,
    ActorContextResolutionInput,
    ActorContextResolutionStatus,
)


def test_resolution_input_is_frozen_strict_and_redacted() -> None:
    payload = ActorContextResolutionInput(
        request_id="request-1",
        trace_id="trace-1",
        correlation_id="corr-1",
        metadata={"safe": {"nested": ("value",)}},
    )

    with pytest.raises(ValidationError):
        ActorContextResolutionInput(request_id="request-1", unexpected=True)  # type: ignore[call-arg]
    with pytest.raises(ValidationError, match="protected material"):
        ActorContextResolutionInput(metadata={"Authorization-Header": "Bearer value"})
    with pytest.raises(ValidationError):
        payload.request_id = "request-2"  # type: ignore[misc]


def test_resolution_status_rejects_unknown_reason_codes_and_is_fingerprinted() -> None:
    status = ActorContextResolutionStatus(
        status_id="status-1",
        source="anonymous_fail_closed",
        reason_codes=REQUIRED_REASON_CODES,
        created_at=datetime(2026, 7, 17, tzinfo=UTC),
    )
    same = ActorContextResolutionStatus(
        status_id="status-1",
        source="anonymous_fail_closed",
        reason_codes=REQUIRED_REASON_CODES,
        created_at=datetime(2026, 7, 17, tzinfo=UTC),
    )

    assert status.fingerprint == same.fingerprint
    with pytest.raises(ValidationError):
        ActorContextResolutionStatus(
            status_id="status-2",
            source="anonymous_fail_closed",
            reason_codes=("unknown_reason",),
            created_at=datetime(2026, 7, 17, tzinfo=UTC),
        )
