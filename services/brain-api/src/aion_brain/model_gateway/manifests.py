"""Immutable model-gateway provider and model manifest registries."""

from __future__ import annotations

from collections.abc import Iterable

from aion_brain.contracts.model_gateway import (
    DETERMINISTIC_PROVIDER_ID,
    MAXIMUM_MODEL_MANIFESTS,
    MAXIMUM_PROVIDER_MANIFESTS,
    REFERENCE_JSON_MODEL_ID,
    REFERENCE_TEXT_MODEL_ID,
    ModelCapabilityProfile,
    ModelGatewayOperation,
    ModelGatewayOutputMode,
    ModelManifest,
    ModelProviderManifest,
)


def deterministic_reference_provider_manifest() -> ModelProviderManifest:
    """Return the single AION-233 provider manifest."""

    return ModelProviderManifest()


def reference_text_model_manifest() -> ModelManifest:
    """Return the text simulation model manifest."""

    return ModelManifest(
        model_id=REFERENCE_TEXT_MODEL_ID,
        supported_operations=(ModelGatewayOperation.text_generate_simulate,),
        output_modes=(ModelGatewayOutputMode.text,),
    )


def reference_json_model_manifest() -> ModelManifest:
    """Return the structured JSON simulation model manifest."""

    return ModelManifest(
        model_id=REFERENCE_JSON_MODEL_ID,
        supported_operations=(
            ModelGatewayOperation.text_generate_simulate,
            ModelGatewayOperation.structured_generate_simulate,
        ),
        output_modes=(ModelGatewayOutputMode.text, ModelGatewayOutputMode.structured_json),
    )


def default_model_manifests() -> tuple[ModelManifest, ModelManifest]:
    """Return the deterministic model manifest allowlist."""

    return (reference_json_model_manifest(), reference_text_model_manifest())


def capability_profile_for_model(model_manifest: ModelManifest) -> ModelCapabilityProfile:
    """Return a no-effect capability profile for a model manifest."""

    return ModelCapabilityProfile(
        profile_id=f"profile-{model_manifest.model_id}",
        provider_id=model_manifest.provider_id,
        model_id=model_manifest.model_id,
        supported_operations=model_manifest.supported_operations,
        output_modes=model_manifest.output_modes,
        maximum_input_tokens=model_manifest.maximum_input_tokens,
        maximum_output_tokens=model_manifest.maximum_output_tokens,
        maximum_response_bytes=model_manifest.maximum_response_bytes,
    )


class InMemoryModelProviderManifestRegistry:
    """Copy-on-write provider manifest registry with a closed allowlist."""

    def __init__(self, manifests: Iterable[ModelProviderManifest] | None = None) -> None:
        selected = tuple(manifests or (deterministic_reference_provider_manifest(),))
        if len(selected) > MAXIMUM_PROVIDER_MANIFESTS:
            raise ValueError("provider manifest count exceeds AION-232-SRI-0002 limit")
        by_id = {manifest.provider_id: manifest for manifest in selected}
        if len(by_id) != len(selected):
            raise ValueError("provider IDs must be unique")
        if set(by_id) != {DETERMINISTIC_PROVIDER_ID}:
            raise ValueError("provider allowlist is closed to deterministic reference provider")
        self._manifests = dict(sorted(by_id.items()))

    def list_manifests(self) -> tuple[ModelProviderManifest, ...]:
        """Return manifests in deterministic order."""

        return tuple(self._manifests[key] for key in sorted(self._manifests))

    def get(self, provider_id: str) -> ModelProviderManifest:
        """Return a provider manifest or fail closed."""

        if provider_id not in self._manifests:
            raise ValueError("unknown provider")
        return self._manifests[provider_id]

    def with_manifest(
        self, manifest: ModelProviderManifest
    ) -> InMemoryModelProviderManifestRegistry:
        """Return a new registry containing the supplied manifest."""

        next_manifests = {**self._manifests, manifest.provider_id: manifest}
        return InMemoryModelProviderManifestRegistry(next_manifests.values())


class InMemoryModelManifestRegistry:
    """Copy-on-write model manifest registry with a closed allowlist."""

    def __init__(self, manifests: Iterable[ModelManifest] | None = None) -> None:
        selected = tuple(manifests or default_model_manifests())
        if len(selected) > MAXIMUM_MODEL_MANIFESTS:
            raise ValueError("model manifest count exceeds AION-232-SRI-0002 limit")
        by_id = {manifest.model_id: manifest for manifest in selected}
        if len(by_id) != len(selected):
            raise ValueError("model IDs must be unique")
        if set(by_id) != {REFERENCE_JSON_MODEL_ID, REFERENCE_TEXT_MODEL_ID}:
            raise ValueError("model allowlist is closed to deterministic reference models")
        if any(manifest.provider_id != DETERMINISTIC_PROVIDER_ID for manifest in selected):
            raise ValueError("model provider reference mismatch")
        self._manifests = dict(sorted(by_id.items()))

    def list_manifests(self) -> tuple[ModelManifest, ...]:
        """Return manifests in deterministic order."""

        return tuple(self._manifests[key] for key in sorted(self._manifests))

    def list_profiles(self) -> tuple[ModelCapabilityProfile, ...]:
        """Return capability profiles in deterministic order."""

        return tuple(capability_profile_for_model(item) for item in self.list_manifests())

    def get(self, model_id: str) -> ModelManifest:
        """Return a model manifest or fail closed."""

        if model_id not in self._manifests:
            raise ValueError("unknown model")
        return self._manifests[model_id]

    def with_manifest(self, manifest: ModelManifest) -> InMemoryModelManifestRegistry:
        """Return a new registry containing the supplied manifest."""

        next_manifests = {**self._manifests, manifest.model_id: manifest}
        return InMemoryModelManifestRegistry(next_manifests.values())
