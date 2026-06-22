"""Resource registry contract tests."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from aion_brain.contracts.resource_references import ResourceReferenceLink
from aion_brain.contracts.resource_registry import (
    ResourceDescriptor,
    ResourceRegistryQuery,
)
from tests.resource_registry_helpers import descriptor


def test_resource_descriptor_requires_aion_uri() -> None:
    payload = descriptor().model_dump(mode="python")
    payload["resource_uri"] = "https://example.invalid/resource"

    with pytest.raises(ValidationError):
        ResourceDescriptor(**payload)


def test_resource_descriptor_rejects_secret_like_metadata() -> None:
    payload = descriptor().model_dump(mode="python")
    payload["metadata"] = {"api_key": "sk-test"}

    with pytest.raises(ValueError):
        ResourceDescriptor(**payload)


def test_resource_link_validates_confidence_bounds() -> None:
    with pytest.raises(ValidationError):
        ResourceReferenceLink(
            resource_link_id="link-1",
            source_resource_uri="aion://generic/source",
            target_resource_uri="aion://generic/target",
            source_type="generic",
            source_id="source",
            target_type="generic",
            target_id="target",
            confidence=1.1,
            discovered_by="test",
        )


def test_registry_query_requires_scope_and_limit_bounds() -> None:
    with pytest.raises(ValidationError):
        ResourceRegistryQuery(scope=[], limit=1)
    with pytest.raises(ValidationError):
        ResourceRegistryQuery(scope=["workspace:main"], limit=1001)
