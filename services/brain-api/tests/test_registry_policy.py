"""Registry policy boundary tests."""

from __future__ import annotations

import pytest

from aion_brain.contracts.resource_registry import ResourceIndexUpsertRequest
from aion_brain.resource_registry.service import ResourceRegistryService
from tests.resource_registry_helpers import DenyPolicy, descriptor, repository


def test_registry_write_fails_closed_when_policy_denies() -> None:
    service = ResourceRegistryService(repository(), DenyPolicy())

    with pytest.raises(PermissionError):
        service.upsert(ResourceIndexUpsertRequest(descriptor=descriptor()))
