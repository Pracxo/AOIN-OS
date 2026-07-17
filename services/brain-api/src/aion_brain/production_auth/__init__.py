"""Internal disabled production-auth core package."""

from __future__ import annotations

from typing import Any

__all__ = [
    "DisabledRequestIdentityVerifier",
    "OfflineEd25519IdentityAssertionVerifier",
    "ProductionAuthRequestIdentityBoundary",
    "ProductionAuthRequestIdentityMiddleware",
    "ProductionAuthAuditBuilder",
    "ProductionAuthActorContextResolver",
    "ProductionAuthCoreService",
    "ProductionAuthDiagnosticBuilder",
    "ProductionAuthPolicyEvaluator",
    "ProductionAuthProvenanceBuilder",
    "RequestIdentityVerifier",
    "TrustedPublicKeyRegistry",
    "canonical_json_bytes",
    "canonical_json_text",
    "production_auth_core_config_from_settings",
    "reason_code_registry_payload",
    "register_production_auth_request_identity_middleware",
    "sha256_fingerprint",
]


def __getattr__(name: str) -> Any:
    if name == "ProductionAuthAuditBuilder":
        from aion_brain.production_auth.audit import ProductionAuthAuditBuilder

        return ProductionAuthAuditBuilder
    if name == "ProductionAuthCoreService":
        from aion_brain.production_auth.core import ProductionAuthCoreService

        return ProductionAuthCoreService
    if name == "ProductionAuthActorContextResolver":
        from aion_brain.production_auth.actor_context import (
            ProductionAuthActorContextResolver,
        )

        return ProductionAuthActorContextResolver
    if name == "OfflineEd25519IdentityAssertionVerifier":
        from aion_brain.production_auth.identity_assertion_verifier import (
            OfflineEd25519IdentityAssertionVerifier,
        )

        return OfflineEd25519IdentityAssertionVerifier
    if name == "TrustedPublicKeyRegistry":
        from aion_brain.production_auth.trusted_public_keys import (
            TrustedPublicKeyRegistry,
        )

        return TrustedPublicKeyRegistry
    if name == "DisabledRequestIdentityVerifier":
        from aion_brain.production_auth.verifier import DisabledRequestIdentityVerifier

        return DisabledRequestIdentityVerifier
    if name == "ProductionAuthRequestIdentityBoundary":
        from aion_brain.production_auth.request_boundary import (
            ProductionAuthRequestIdentityBoundary,
        )

        return ProductionAuthRequestIdentityBoundary
    if name == "ProductionAuthRequestIdentityMiddleware":
        from aion_brain.production_auth.request_middleware import (
            ProductionAuthRequestIdentityMiddleware,
        )

        return ProductionAuthRequestIdentityMiddleware
    if name == "register_production_auth_request_identity_middleware":
        from aion_brain.production_auth.request_middleware import (
            register_production_auth_request_identity_middleware,
        )

        return register_production_auth_request_identity_middleware
    if name == "RequestIdentityVerifier":
        from aion_brain.production_auth.verifier import RequestIdentityVerifier

        return RequestIdentityVerifier
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
