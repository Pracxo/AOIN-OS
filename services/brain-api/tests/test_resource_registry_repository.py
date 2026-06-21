"""Resource registry repository tests."""

from __future__ import annotations

from aion_brain.contracts.resource_registry import ResourceIndexRecord, ResourceRegistryQuery
from tests.resource_registry_helpers import descriptor, repository


def test_repository_saves_and_gets_resource_by_uri() -> None:
    repo = repository()
    record = repo.save_resource(
        ResourceIndexRecord(resource_index_id="idx-1", descriptor=descriptor())
    )

    fetched = repo.get_resource_by_uri(record.descriptor.resource_uri)

    assert fetched is not None
    assert fetched.resource_index_id == "idx-1"


def test_repository_lists_resources_with_scope_filter() -> None:
    repo = repository()
    repo.save_resource(ResourceIndexRecord(resource_index_id="idx-1", descriptor=descriptor()))

    result = repo.list_resources(ResourceRegistryQuery(scope=["workspace:main"], limit=10))

    assert [item.resource_index_id for item in result] == ["idx-1"]


def test_repository_gets_resource_by_type_id() -> None:
    repo = repository()
    repo.save_resource(ResourceIndexRecord(resource_index_id="idx-1", descriptor=descriptor("abc")))

    assert repo.get_resource_by_type_id("generic", "abc") is not None
