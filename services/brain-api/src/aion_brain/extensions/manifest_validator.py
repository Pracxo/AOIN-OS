"""Metadata-only extension manifest validation."""

from __future__ import annotations

from typing import Any

from aion_brain.config import Settings, get_settings
from aion_brain.contracts.extensions import ExtensionManifest
from aion_brain.extensions.hash import hash_manifest
from aion_brain.extensions.redaction import redact_extension_payload, reject_executable_payload

_DOMAIN_PACKAGE_TYPES = {
    "finance",
    "trading",
    "legal",
    "health",
    "healthcare",
    "hr",
    "procurement",
}


class ManifestValidator:
    """Validate extension metadata without loading or executing extension code."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()

    def validate(self, manifest: ExtensionManifest) -> dict[str, Any]:
        """Return deterministic validation result for one manifest."""

        findings: list[dict[str, Any]] = []
        blockers: list[dict[str, Any]] = []
        warnings: list[dict[str, Any]] = []
        payload = manifest.model_dump(mode="json")
        try:
            reject_executable_payload(payload)
        except ValueError as exc:
            blockers.append(_finding("executable_payload", "critical", str(exc)))
        if manifest.package_type in _DOMAIN_PACKAGE_TYPES:
            blockers.append(
                _finding(
                    "domain_package_type",
                    "critical",
                    "Extension package type must remain generic.",
                )
            )
        if not self._settings.extension_manifest_validation_enabled:
            blockers.append(
                _finding(
                    "manifest_validation_disabled",
                    "high",
                    "Extension manifest validation is disabled.",
                )
            )
        if manifest.declared_routes:
            warnings.append(
                _finding(
                    "routes_declaration_only",
                    "medium",
                    "Declared routes are metadata only and are never registered dynamically.",
                )
            )
        if manifest.declared_policy_actions:
            warnings.append(
                _finding(
                    "policy_actions_declaration_only",
                    "medium",
                    "Declared policy actions require explicit AION core implementation.",
                )
            )
        status = "blocked" if blockers else "warning" if warnings else "passed"
        return {
            "status": status,
            "manifest_hash": hash_manifest(payload),
            "findings": findings,
            "blockers": blockers,
            "warnings": warnings,
            "normalized_manifest": redact_extension_payload(payload),
            "metadata": {
                "metadata_only": True,
                "code_loading_enabled": self._settings.extension_code_loading_enabled,
                "activation_enabled": self._settings.extension_activation_enabled,
                "external_sources_enabled": self._settings.extension_external_sources_enabled,
            },
        }


def _finding(code: str, severity: str, message: str) -> dict[str, Any]:
    return {"code": code, "severity": severity, "message": message}


__all__ = ["ManifestValidator"]
