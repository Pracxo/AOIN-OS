"""Consistency and lease API tests."""

from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient

from aion_brain.api.consistency import get_consistency_checker, get_processing_lease_service
from aion_brain.contracts.consistency import ConsistencyCheckResult, ProcessingLease
from aion_brain.main import app


class FakeChecker:
    """Consistency checker fake."""

    def run(self, request):  # type: ignore[no-untyped-def]
        return ConsistencyCheckResult(
            consistency_check_id="consistency-1",
            check_type=request.check_type,
            status="passed",
            scope=request.scope,
            violations=[],
            repaired=False,
            result={},
            created_at=datetime.now(UTC),
            completed_at=datetime.now(UTC),
        )


class FakeLeaseService:
    """Lease service fake."""

    def acquire(self, resource_type, resource_id, owner_id, ttl_seconds=None):  # type: ignore[no-untyped-def]
        return lease(resource_type=resource_type, resource_id=resource_id, owner_id=owner_id)

    def release(self, lease_id, owner_id):  # type: ignore[no-untyped-def]
        return lease(status="released", owner_id=owner_id, lease_id=lease_id)


def test_consistency_api_works() -> None:
    """Consistency and lease APIs work."""
    app.dependency_overrides[get_consistency_checker] = lambda: FakeChecker()
    app.dependency_overrides[get_processing_lease_service] = lambda: FakeLeaseService()
    try:
        client = TestClient(app)
        response = client.post(
            "/brain/consistency/check",
            json={"check_type": "kernel_boundary", "scope": ["workspace:main"]},
        )
        assert response.status_code == 200
        assert response.json()["status"] == "passed"

        lease_response = client.post(
            "/brain/leases/acquire",
            json={"resource_type": "outbox", "resource_id": "outbox-1", "owner_id": "worker"},
        )
        assert lease_response.status_code == 200
        assert lease_response.json()["status"] == "active"
    finally:
        app.dependency_overrides.clear()


def lease(
    *,
    status: str = "active",
    resource_type: str = "outbox",
    resource_id: str = "outbox-1",
    owner_id: str = "worker",
    lease_id: str = "lease-1",
) -> ProcessingLease:
    return ProcessingLease(
        lease_id=lease_id,
        resource_type=resource_type,
        resource_id=resource_id,
        owner_id=owner_id,
        status=status,  # type: ignore[arg-type]
        expires_at=datetime.now(UTC) + timedelta(minutes=5),
        metadata={},
        created_at=datetime.now(UTC),
    )
