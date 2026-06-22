"""Resource link service tests."""

from __future__ import annotations

from aion_brain.contracts.resource_references import ResourceReferenceCreateRequest
from aion_brain.resource_registry.links import ResourceLinkService
from tests.kernel_fakes import AllowPolicy
from tests.resource_registry_helpers import FakeTelemetry, repository


def test_link_service_creates_link_and_backlink() -> None:
    repo = repository()
    telemetry = FakeTelemetry()
    service = ResourceLinkService(repo, AllowPolicy(), telemetry_service=telemetry)

    link = service.create_link(
        ResourceReferenceCreateRequest(
            source_resource_uri="aion://generic/source",
            target_resource_uri="aion://generic/target",
            relation_type="references",
        ),
        ["workspace:main"],
    )

    assert link.source_type == "generic"
    assert repo.list_backlinks("aion://generic/target")
    assert telemetry.events[0].event_type == "resource_link_created"


def test_link_service_marks_link_broken() -> None:
    repo = repository()
    service = ResourceLinkService(repo, AllowPolicy())
    link = service.create_link(
        ResourceReferenceCreateRequest(
            source_resource_uri="aion://generic/source",
            target_resource_uri="aion://generic/target",
        ),
        ["workspace:main"],
    )

    broken = service.mark_broken(link.resource_link_id, "missing target")

    assert broken.status == "broken"
