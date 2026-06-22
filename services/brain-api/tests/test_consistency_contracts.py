"""Consistency contract tests."""

from datetime import UTC, datetime

import pytest

from aion_brain.contracts.consistency import ConsistencyCheckRequest, ProcessingLease


def test_processing_lease_validates_status() -> None:
    """Processing lease status is constrained."""
    with pytest.raises(ValueError):
        ProcessingLease(
            lease_id="lease-1",
            resource_type="outbox",
            resource_id="outbox-1",
            owner_id="worker",
            status="unknown",  # type: ignore[arg-type]
            expires_at=datetime.now(UTC),
        )


def test_consistency_check_request_validates_check_type() -> None:
    """Consistency check type is constrained."""
    with pytest.raises(ValueError):
        ConsistencyCheckRequest(
            check_type="unknown",  # type: ignore[arg-type]
            scope=["workspace:main"],
        )
