"""Registry audit-boundary tests."""

from __future__ import annotations

from aion_brain.contracts.resource_registry import ResourceIndexUpsertRequest
from aion_brain.resource_registry.service import ResourceRegistryService
from tests.kernel_fakes import AllowPolicy
from tests.resource_registry_helpers import descriptor, repository


def test_registry_records_index_metadata_not_source_truth() -> None:
    record = ResourceRegistryService(repository(), AllowPolicy()).upsert(
        ResourceIndexUpsertRequest(descriptor=descriptor())
    )

    assert record.descriptor.metadata["registry_source_of_truth"] is False
    assert record.descriptor.metadata["source_records_mutated"] is False
