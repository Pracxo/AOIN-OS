"""Capability registry contracts and adapter interface."""

from typing import Any, Protocol

from aion_brain.contracts.capabilities import CapabilityManifest


class CapabilityProtocolAdapter(Protocol):
    """Interface for future capability protocols."""

    def list_capabilities(self) -> list[CapabilityManifest]:
        """List available capabilities."""
        ...

    def invoke(self, capability_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Invoke a capability by ID."""
        ...


class CapabilityRegistry:
    """In-memory manifest registry for scaffold tests and future expansion."""

    def __init__(self) -> None:
        self._manifests: dict[str, CapabilityManifest] = {}

    def register(self, manifest: CapabilityManifest) -> None:
        """Register a capability manifest."""
        self._manifests[_manifest_key(manifest.module_id, manifest.version)] = manifest

    def list_manifests(self) -> list[CapabilityManifest]:
        """Return registered manifests."""
        return list(self._manifests.values())

    def get_manifest(self, module_id: str, version: str | None = None) -> CapabilityManifest | None:
        """Return a manifest by module ID and optional version."""
        if version is not None:
            return self._manifests.get(_manifest_key(module_id, version))
        for manifest in self._manifests.values():
            if manifest.module_id == module_id:
                return manifest
        return None

    def capability_exists(self, capability_id: str) -> bool:
        """Return whether the registry contains a capability."""
        return any(
            _capability_id(capability) == capability_id
            for manifest in self._manifests.values()
            for capability in manifest.capabilities
        )


def _manifest_key(module_id: str, version: str) -> str:
    return f"{module_id}:{version}"


def _capability_id(capability: object) -> str | None:
    if isinstance(capability, dict):
        value = capability.get("capability_id") or capability.get("id")
        if isinstance(value, str):
            return value
    value = getattr(capability, "capability_id", None)
    if isinstance(value, str):
        return value
    return None
