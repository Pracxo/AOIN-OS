from __future__ import annotations

import pytest
from capability_runtime_test_support import load_runtime
from pydantic import ValidationError


def test_closed_capability_and_connector_manifests_are_exact() -> None:
    runtime = load_runtime()
    manifests = runtime.CAPABILITY_MANIFESTS
    assert [item.capability_id for item in manifests] == [
        "capability_runtime.health.read",
        "capability_runtime.observability.read",
        "capability_runtime.audit.read",
        "capability.text.normalize",
        "capability.hash.sha256",
        "capability.json.validate",
        "connector.reference.read.simulate",
        "connector.reference.write.preview",
    ]
    assert len({item.manifest_fingerprint for item in manifests}) == 8
    assert all(item.operator_invoked and item.explicit_plan for item in manifests)
    assert all(item.sandboxed and item.deterministic for item in manifests)
    assert all(not item.external_effect and not item.production_effect for item in manifests)
    assert all(not item.network_effect and not item.filesystem_effect for item in manifests)
    assert all(not item.process_effect and not item.credential_effect for item in manifests)
    assert all(not item.token_effect and not item.actual_tool_execution for item in manifests)
    assert sum(1 for item in manifests if item.approval_required) == 3

    connector = runtime.CONNECTOR_MANIFEST
    assert connector.connector_id == "deterministic-reference-fixture-connector"
    assert connector.supported_operations == (
        "connector.reference.read.simulate",
        "connector.reference.write.preview",
    )
    assert connector.credential_free is True
    assert connector.endpoint_present is False
    assert connector.network_enabled is False
    assert connector.filesystem_enabled is False
    assert connector.process_enabled is False
    assert connector.actual_connector_available is False
    assert connector.synthetic_only is True
    assert connector.in_memory_only is True


def test_manifest_tampering_and_downgrade_are_rejected() -> None:
    runtime = load_runtime()
    manifest = runtime.CAPABILITY_MANIFESTS[2].model_dump(mode="json")
    manifest["approval_required"] = False
    with pytest.raises(ValueError, match="fingerprint"):
        runtime.CapabilityManifest(**manifest)

    connector = runtime.CONNECTOR_MANIFEST.model_dump(mode="json")
    connector["endpoint_present"] = True
    with pytest.raises(ValidationError):
        runtime.ConnectorManifest(**connector)
