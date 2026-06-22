"""Capability registry service."""

from aion_brain.capabilities.registry import CapabilityRegistry
from aion_brain.contracts.capabilities import CapabilityManifest


class CapabilityService:
    """Service facade for capability manifest registration and lookup."""

    def __init__(self, registry: CapabilityRegistry) -> None:
        self._registry = registry

    def register_manifest(self, manifest: CapabilityManifest) -> CapabilityManifest:
        """Register a capability manifest."""
        self._registry.register(manifest)
        return manifest

    def list_manifests(self) -> list[CapabilityManifest]:
        """Return capability manifests."""
        return self._registry.list_manifests()

    def list_capabilities(self) -> list[dict[str, object]]:
        """Return flattened capability dictionaries."""
        capabilities: list[dict[str, object]] = []
        for manifest in self._registry.list_manifests():
            for capability in manifest.capabilities:
                if isinstance(capability, dict):
                    capabilities.append(
                        {
                            **capability,
                            "module_id": manifest.module_id,
                            "version": manifest.version,
                        }
                    )
        return capabilities

    def capability_exists(self, capability_id: str) -> bool:
        """Return whether a capability is registered."""
        return self._registry.capability_exists(capability_id)

    def validate_manifest_contract(self, manifest: CapabilityManifest) -> bool:
        """Return whether a manifest is structurally present for certification."""

        return bool(manifest.module_id and manifest.version and manifest.capabilities)
