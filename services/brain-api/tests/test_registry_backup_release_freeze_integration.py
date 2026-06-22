"""Registry backup/release/freeze integration tests."""

from __future__ import annotations

from aion_brain.resource_registry.descriptors import ResourceDescriptorFactory
from aion_brain.resource_registry.scanners import ResourceScanner


class Provider:
    def __init__(self, resource_type: str) -> None:
        self._resource_type = resource_type

    def list_registry_records(self, limit: int = 100) -> list[dict[str, object]]:
        return [
            {
                "id": f"{self._resource_type}-1",
                "resource_type": self._resource_type,
                "owner_scope": ["workspace:main"],
                "title": f"{self._resource_type} record",
                "summary": "Registry descriptor only.",
            }
        ]


def test_scanner_accepts_backup_release_and_freeze_providers() -> None:
    scanner = ResourceScanner(
        ResourceDescriptorFactory(),
        backup=Provider("backup_job"),
        release=Provider("release_package"),
        freeze=Provider("freeze_gate"),
    )

    descriptors = scanner.scan([], [], ["workspace:main"], 10)

    assert {item.resource_type for item in descriptors} == {
        "backup_job",
        "freeze_gate",
        "release_package",
    }
