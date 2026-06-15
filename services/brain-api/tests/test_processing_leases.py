"""Processing lease tests."""

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from aion_brain.config import Settings
from aion_brain.consistency.leases import ProcessingLeaseService
from aion_brain.consistency.repository import ConsistencyRepository


def test_processing_lease_acquires_lease() -> None:
    """A lease can be acquired."""
    service = make_service()

    lease = service.acquire("outbox", "outbox-1", "worker")

    assert lease.status == "active"


def test_processing_lease_prevents_duplicate_active_lease() -> None:
    """Duplicate active leases are blocked."""
    service = make_service()
    service.acquire("outbox", "outbox-1", "worker")

    with pytest.raises(ValueError):
        service.acquire("outbox", "outbox-1", "worker-2")


def test_processing_lease_allows_acquire_after_expiry() -> None:
    """Expired active lease can be replaced."""
    service = make_service()
    service.acquire("outbox", "outbox-1", "worker", ttl_seconds=1)

    expired = service.expire_old(datetime.now(UTC) + timedelta(seconds=2))
    lease = service.acquire("outbox", "outbox-1", "worker-2")

    assert expired == 1
    assert lease.owner_id == "worker-2"


def make_service() -> ProcessingLeaseService:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    settings = Settings(_env_file=None, DATABASE_URL="sqlite+pysqlite:///:memory:")
    return ProcessingLeaseService(ConsistencyRepository(engine=engine), settings=settings)
