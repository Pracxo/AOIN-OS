"""Consistency checker tests."""

from datetime import UTC, datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from aion_brain.config import Settings
from aion_brain.consistency.checker import ConsistencyChecker
from aion_brain.consistency.leases import ProcessingLeaseService
from aion_brain.consistency.repository import ConsistencyRepository
from aion_brain.contracts.consistency import ConsistencyCheckRequest
from aion_brain.contracts.outbox import OutboxPublishRequest
from aion_brain.outbox.repository import OutboxRepository
from aion_brain.outbox.service import OutboxService


def test_consistency_checker_detects_stale_processing_lease() -> None:
    """Checker reports active leases past expiry."""
    checker, lease_service, _outbox, repository = make_checker()
    lease = lease_service.acquire("outbox", "outbox-1", "worker")
    repository.save_lease(
        lease.model_copy(update={"expires_at": datetime.now(UTC) - timedelta(seconds=1)})
    )

    result = checker.run(
        ConsistencyCheckRequest(check_type="stale_processing_leases", scope=["workspace:main"])
    )

    assert result.violations
    assert result.violations[0]["type"] == "stale_processing_lease"


def test_consistency_checker_repair_expires_stale_lease() -> None:
    """Repair expires stale leases."""
    checker, lease_service, _outbox, repository = make_checker()
    lease = lease_service.acquire("outbox", "outbox-1", "worker")
    repository.save_lease(
        lease.model_copy(update={"expires_at": datetime.now(UTC) - timedelta(seconds=1)})
    )

    result = checker.run(
        ConsistencyCheckRequest(
            check_type="stale_processing_leases",
            scope=["workspace:main"],
            repair=True,
            metadata={"now": "future"},
        )
    )

    assert result.status == "repaired"
    assert lease_service.get_active("outbox", "outbox-1") is None


def test_consistency_checker_detects_stuck_outbox() -> None:
    """Checker reports pending outbox messages older than threshold."""
    checker, _lease_service, outbox, _repository = make_checker()
    message = outbox.enqueue(
        OutboxPublishRequest(
            message_type="event.publish",
            destination="noop",
            payload={"event_id": "event-1"},
        )
    )
    outbox._repository.save(  # noqa: SLF001
        message.model_copy(update={"created_at": datetime.now(UTC) - timedelta(minutes=10)})
    )

    result = checker.run(
        ConsistencyCheckRequest(check_type="outbox_stuck", scope=["workspace:main"])
    )

    assert result.violations
    assert result.violations[0]["type"] == "stuck_outbox"


def make_checker() -> tuple[
    ConsistencyChecker,
    ProcessingLeaseService,
    OutboxService,
    ConsistencyRepository,
]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    settings = Settings(_env_file=None, DATABASE_URL="sqlite+pysqlite:///:memory:")
    repository = ConsistencyRepository(engine=engine)
    lease_service = ProcessingLeaseService(repository, settings=settings)
    outbox = OutboxService(OutboxRepository(engine=engine), settings=settings)
    checker = ConsistencyChecker(
        repository=repository,
        lease_service=lease_service,
        outbox_service=outbox,
        settings=settings,
    )
    return checker, lease_service, outbox, repository
