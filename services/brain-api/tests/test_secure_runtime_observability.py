from __future__ import annotations

from aion_brain.contracts.secure_runtime import SecureRuntimeIntegrityStatus
from tests.secure_runtime_test_support import secure_runtime_fixture


def test_observability_and_health_are_redacted_local_snapshots() -> None:
    fixture = secure_runtime_fixture()
    snapshot = fixture.service.observability_snapshot(
        session=fixture.session,
        usage=fixture.usage,
        integrity_status=SecureRuntimeIntegrityStatus.passed,
    )
    health = fixture.service.health_snapshot(session_id=fixture.session.session_id)

    assert snapshot.external_telemetry_exporter is False
    assert snapshot.network_export is False
    assert snapshot.redacted is True
    assert health.production_runtime is False
    assert health.providers is False
    assert health.tools is False
