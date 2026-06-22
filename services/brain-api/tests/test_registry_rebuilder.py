"""Registry rebuilder tests."""

from __future__ import annotations

from aion_brain.contracts.resource_registry import RegistryRebuildRequest
from aion_brain.resource_registry.descriptors import ResourceDescriptorFactory
from aion_brain.resource_registry.links import ResourceLinkService
from aion_brain.resource_registry.rebuilder import RegistryRebuilder
from aion_brain.resource_registry.scanners import ResourceScanner
from aion_brain.resource_registry.service import ResourceRegistryService
from aion_brain.resource_registry.snapshots import RegistrySnapshotService
from tests.kernel_fakes import AllowPolicy
from tests.resource_registry_helpers import descriptor, repository


class Provider:
    def list_registry_records(self, limit: int = 100) -> list[dict[str, object]]:
        return [descriptor("provider-record").model_dump(mode="python")]


def test_registry_rebuilder_dry_run_has_no_index_side_effect() -> None:
    repo = repository()
    scanner = ResourceScanner(ResourceDescriptorFactory(), test=Provider())
    rebuilder = _rebuilder(repo, scanner)

    run = rebuilder.rebuild(RegistryRebuildRequest(owner_scope=["workspace:main"]))

    assert run.status == "dry_run"
    assert run.resources_seen == 1
    assert repo.list_resources(limit=10) == []


def test_registry_rebuilder_controlled_indexes_resources() -> None:
    repo = repository()
    scanner = ResourceScanner(ResourceDescriptorFactory(), test=Provider())
    rebuilder = _rebuilder(repo, scanner)

    run = rebuilder.rebuild(
        RegistryRebuildRequest(owner_scope=["workspace:main"], mode="controlled")
    )

    assert run.resources_indexed == 1
    assert repo.list_resources(limit=10)


def _rebuilder(repo: object, scanner: ResourceScanner) -> RegistryRebuilder:
    registry_service = ResourceRegistryService(repo, AllowPolicy())
    link_service = ResourceLinkService(repo, AllowPolicy())
    snapshot_service = RegistrySnapshotService(repo, AllowPolicy())
    return RegistryRebuilder(
        repo,
        AllowPolicy(),
        scanner=scanner,
        registry_service=registry_service,
        link_service=link_service,
        snapshot_service=snapshot_service,
    )
