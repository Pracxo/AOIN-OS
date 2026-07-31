from __future__ import annotations

import pytest

from aion_brain.contracts.model_gateway import (
    ModelGatewayOperation,
    ModelGatewayOutputMode,
    ModelManifest,
)
from aion_brain.model_gateway.manifests import InMemoryModelManifestRegistry


def test_model_manifest_registry_contains_exact_reference_models() -> None:
    registry = InMemoryModelManifestRegistry()
    assert [item.model_id for item in registry.list_manifests()] == [
        "reference-json-sim-v1",
        "reference-text-sim-v1",
    ]
    for manifest in registry.list_manifests():
        assert manifest.provider_id == "deterministic-reference-provider"
        assert manifest.simulation_only is True
        assert manifest.actual_provider_call is False
        assert manifest.tool_calling is False
        assert manifest.function_calling is False


def test_model_substitution_is_rejected() -> None:
    with pytest.raises(ValueError):
        ModelManifest(
            model_id="other-model",
            supported_operations=(ModelGatewayOperation.text_generate_simulate,),
            output_modes=(ModelGatewayOutputMode.text,),
        )
