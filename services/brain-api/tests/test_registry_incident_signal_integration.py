"""Registry incident-signal integration tests."""

from __future__ import annotations

from aion_brain.contracts.resource_references import ResourceReferenceCreateRequest
from aion_brain.contracts.resource_registry import ReferenceValidationRequest, ResourceIndexRecord
from aion_brain.resource_registry.links import ResourceLinkService
from aion_brain.resource_registry.validator import ReferenceValidator
from tests.kernel_fakes import AllowPolicy
from tests.resource_registry_helpers import descriptor, repository


class FakeIncidentSignalService:
    def __init__(self) -> None:
        self.requests: list[object] = []

    def create_signal(self, request: object) -> object:
        self.requests.append(request)
        return request


def test_validator_can_create_incident_signal_for_integrity_findings() -> None:
    repo = repository()
    repo.save_resource(
        ResourceIndexRecord(resource_index_id="idx-source", descriptor=descriptor("source"))
    )
    ResourceLinkService(repo, AllowPolicy()).create_link(
        ResourceReferenceCreateRequest(
            source_resource_uri="aion://generic/source",
            target_resource_uri="aion://generic/missing",
        ),
        ["workspace:main"],
    )
    incidents = FakeIncidentSignalService()

    ReferenceValidator(
        repo,
        AllowPolicy(),
        incident_signal_service=incidents,
    ).validate(
        ReferenceValidationRequest(
            owner_scope=["workspace:main"],
            mode="controlled",
            create_incident_signals=True,
        )
    )

    assert len(incidents.requests) == 1
