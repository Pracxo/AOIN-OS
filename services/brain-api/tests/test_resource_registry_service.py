"""Resource registry service tests."""

from __future__ import annotations

import pytest

from aion_brain.contracts.resource_registry import ResourceIndexUpsertRequest
from aion_brain.resource_registry.service import ResourceRegistryService
from tests.kernel_fakes import AllowPolicy
from tests.resource_registry_helpers import DenyPolicy, FakeTelemetry, descriptor, repository


def test_registry_service_upserts_resource_and_emits_telemetry() -> None:
    telemetry = FakeTelemetry()
    service = ResourceRegistryService(repository(), AllowPolicy(), telemetry_service=telemetry)

    record = service.upsert(ResourceIndexUpsertRequest(descriptor=descriptor()))

    assert record.descriptor.resource_uri == "aion://generic/res-1"
    assert telemetry.events[0].event_type == "resource_indexed"


def test_policy_deny_blocks_registry_resource_create() -> None:
    service = ResourceRegistryService(repository(), DenyPolicy())

    with pytest.raises(PermissionError):
        service.upsert(ResourceIndexUpsertRequest(descriptor=descriptor()))
