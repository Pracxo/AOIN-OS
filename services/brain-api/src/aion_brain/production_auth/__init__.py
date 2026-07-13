"""Internal disabled production-auth core package."""

from __future__ import annotations

from typing import Any

__all__ = [
    "ProductionAuthAuditBuilder",
    "ProductionAuthCoreService",
    "ProductionAuthDiagnosticBuilder",
    "ProductionAuthPolicyEvaluator",
    "ProductionAuthProvenanceBuilder",
    "canonical_json_bytes",
    "canonical_json_text",
    "production_auth_core_config_from_settings",
    "reason_code_registry_payload",
    "sha256_fingerprint",
]


def __getattr__(name: str) -> Any:
    if name == "ProductionAuthAuditBuilder":
        from aion_brain.production_auth.audit import ProductionAuthAuditBuilder

        return ProductionAuthAuditBuilder
    if name == "ProductionAuthCoreService":
        from aion_brain.production_auth.core import ProductionAuthCoreService

        return ProductionAuthCoreService
    if name == "ProductionAuthDiagnosticBuilder":
        from aion_brain.production_auth.diagnostics import ProductionAuthDiagnosticBuilder

        return ProductionAuthDiagnosticBuilder
    if name == "ProductionAuthPolicyEvaluator":
        from aion_brain.production_auth.policy import ProductionAuthPolicyEvaluator

        return ProductionAuthPolicyEvaluator
    if name == "ProductionAuthProvenanceBuilder":
        from aion_brain.production_auth.provenance import ProductionAuthProvenanceBuilder

        return ProductionAuthProvenanceBuilder
    if name == "production_auth_core_config_from_settings":
        from aion_brain.production_auth.config import production_auth_core_config_from_settings

        return production_auth_core_config_from_settings
    if name in {"canonical_json_bytes", "canonical_json_text", "sha256_fingerprint"}:
        from aion_brain.production_auth import canonical

        return getattr(canonical, name)
    if name == "reason_code_registry_payload":
        from aion_brain.production_auth.reason_codes import reason_code_registry_payload

        return reason_code_registry_payload
    raise AttributeError(name)
