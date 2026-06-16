from __future__ import annotations

from aion_brain.contracts.confidence import IntrospectionSnapshotRequest
from tests.self_model_helpers import bundle


def test_introspection_snapshot_stores_redacted_config_summary_only() -> None:
    services = bundle()

    snapshot = services.introspection.create_snapshot(
        IntrospectionSnapshotRequest(
            owner_scope=["workspace:main"],
            trace_id="trace-1",
            snapshot_type="manual",
        )
    )

    assert snapshot.status == "created"
    assert snapshot.config_summary["redacted"] is True
    assert "database_url" not in snapshot.config_summary
    assert snapshot.self_model["full_name"] == "Adaptive Intelligence Orchestration Nexus"
