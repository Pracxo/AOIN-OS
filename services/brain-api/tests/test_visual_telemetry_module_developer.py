"""Visual telemetry tests for module developer certification."""

from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from aion_brain.module_developer.repository import ModuleDeveloperRepository
from tests.module_developer_fakes import FakeTelemetry, certifier, package_request


def test_visual_telemetry_emits_certification_events() -> None:
    repo = ModuleDeveloperRepository(
        engine=create_engine(
            "sqlite+pysqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
    )
    telemetry = FakeTelemetry()
    service = certifier(repo, telemetry=telemetry)
    package = service.submit_package(package_request())
    request_cls = __import__(
        "aion_brain.contracts.module_developer",
        fromlist=["ModuleCertificationRequest"],
    ).ModuleCertificationRequest

    service.certify(request_cls(module_package_id=package.module_package_id, owner_scope=["scope"]))

    event_types = {getattr(event, "event_type", None) for event in telemetry.events}
    node_types = {getattr(event, "node_type", None) for event in telemetry.events}
    assert "module_certification_completed" in event_types
    assert "certification" in node_types

