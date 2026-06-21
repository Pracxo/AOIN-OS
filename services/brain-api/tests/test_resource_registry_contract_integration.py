"""Resource Registry integration with Contract Registry."""

from __future__ import annotations

from aion_brain.resource_registry.descriptors import ResourceDescriptorFactory
from aion_brain.resource_registry.scanners import ResourceScanner
from tests.contract_registry_helpers import SCOPE, interface_record, repository, snapshot


def test_resource_registry_can_index_contract_snapshot() -> None:
    contract_repo = repository()
    contract_repo.save_snapshot(snapshot("snapshot-1", interfaces=[interface_record()]))
    scanner = ResourceScanner(ResourceDescriptorFactory())
    scanner.set_provider("contract_registry", contract_repo)

    descriptors = scanner.scan(["contract_snapshot"], ["contract_registry"], SCOPE, 10)

    assert descriptors[0].resource_type == "contract_snapshot"
    assert descriptors[0].resource_id == "snapshot-1"
