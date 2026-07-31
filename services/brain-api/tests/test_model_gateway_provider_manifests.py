from __future__ import annotations

import pytest

from aion_brain.contracts.model_gateway import ModelProviderManifest
from aion_brain.model_gateway.manifests import InMemoryModelProviderManifestRegistry


def test_provider_manifest_is_closed_credential_free_and_endpoint_free() -> None:
    manifest = InMemoryModelProviderManifestRegistry().get("deterministic-reference-provider")
    assert manifest.provider_id == "deterministic-reference-provider"
    assert manifest.provider_type == "reference_simulation"
    assert manifest.credential_free is True
    assert manifest.endpoint_present is False
    assert manifest.provider_sdk_enabled is False
    assert manifest.network_egress_enabled is False
    assert manifest.actual_provider_call_available is False


def test_provider_spoofing_is_rejected() -> None:
    with pytest.raises(ValueError):
        InMemoryModelProviderManifestRegistry(
            [ModelProviderManifest(provider_id="spoofed-provider")]
        )
