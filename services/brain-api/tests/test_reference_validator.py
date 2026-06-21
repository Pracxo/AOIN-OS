"""Reference validator tests."""

from __future__ import annotations

from aion_brain.contracts.resource_references import ResourceReferenceCreateRequest
from aion_brain.contracts.resource_registry import (
    ReferenceValidationRequest,
    ResourceIndexRecord,
)
from aion_brain.resource_registry.links import ResourceLinkService
from aion_brain.resource_registry.validator import ReferenceValidator
from tests.kernel_fakes import AllowPolicy
from tests.resource_registry_helpers import FakeTelemetry, descriptor, repository


def test_reference_validator_detects_missing_target() -> None:
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

    run = ReferenceValidator(repo, AllowPolicy()).validate(
        ReferenceValidationRequest(owner_scope=["workspace:main"], mode="controlled")
    )

    assert run.broken_count == 1
    assert repo.list_broken_references()[0].issue_type == "missing_target"


def test_reference_validator_detects_orphaned_resource() -> None:
    repo = repository()
    repo.save_resource(
        ResourceIndexRecord(resource_index_id="idx-orphan", descriptor=descriptor("orphan"))
    )

    run = ReferenceValidator(repo, AllowPolicy()).validate(
        ReferenceValidationRequest(owner_scope=["workspace:main"], mode="controlled")
    )

    assert run.orphaned_count == 1
    assert repo.list_orphaned_resources()[0].issue_type == "no_inbound_refs"


def test_reference_validator_emits_visual_telemetry() -> None:
    repo = repository()
    repo.save_resource(
        ResourceIndexRecord(resource_index_id="idx-orphan", descriptor=descriptor("orphan"))
    )
    telemetry = FakeTelemetry()

    ReferenceValidator(repo, AllowPolicy(), telemetry_service=telemetry).validate(
        ReferenceValidationRequest(owner_scope=["workspace:main"], mode="controlled")
    )

    event_types = [item.event_type for item in telemetry.events]
    assert "reference_validation_started" in event_types
    assert "orphaned_resource_detected" in event_types
    assert "reference_validation_completed" in event_types
