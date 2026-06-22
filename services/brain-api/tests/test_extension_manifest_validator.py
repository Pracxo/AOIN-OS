"""Extension manifest validator tests."""

from __future__ import annotations

from aion_brain.config import Settings
from aion_brain.extensions.manifest_validator import ManifestValidator
from tests.extension_helpers import extension_manifest


def test_manifest_validator_passes_generic_manifest() -> None:
    validator = ManifestValidator(Settings(_env_file=None))

    result = validator.validate(extension_manifest())

    assert result["status"] == "warning"
    assert result["manifest_hash"]
    assert result["metadata"]["code_loading_enabled"] is False
    assert result["metadata"]["activation_enabled"] is False
    assert result["metadata"]["external_sources_enabled"] is False


def test_manifest_validator_warns_for_declared_routes_only() -> None:
    validator = ManifestValidator(Settings(_env_file=None))
    manifest = extension_manifest(declared_routes=[{"path": "/extensions/test"}])

    result = validator.validate(manifest)

    assert result["status"] == "warning"
    assert result["warnings"][0]["code"] == "routes_declaration_only"
