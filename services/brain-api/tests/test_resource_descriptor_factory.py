"""Resource descriptor factory tests."""

from __future__ import annotations

from aion_brain.resource_registry.descriptors import ResourceDescriptorFactory


def test_descriptor_factory_builds_minimal_descriptor() -> None:
    descriptor = ResourceDescriptorFactory().minimal(
        "Generic Resource",
        "resource-1",
        "test",
        ["workspace:main"],
    )

    assert descriptor.resource_uri == "aion://generic/resource-1"
    assert descriptor.owner_scope == ["workspace:main"]
    assert descriptor.metadata["registry_descriptor_only"] is True


def test_descriptor_factory_extracts_safe_refs() -> None:
    descriptor = ResourceDescriptorFactory().from_record(
        "generic",
        {
            "id": "source",
            "refs": ["aion://generic/target"],
            "metadata": {"safe": True},
        },
        "test",
        ["workspace:main"],
    )

    assert descriptor.refs == ["aion://generic/target"]
