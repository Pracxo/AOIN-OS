#!/usr/bin/env python3
"""Validate production-auth authorization lifecycle records."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class AuthorizationSpec:
    transaction_id: str
    approval_record_id: str
    candidate_id: str
    workstream: str
    implementation_task: str
    authorization_scope: str
    task_id: str
    required_adr: str
    expiry: str
    authorization_active: bool
    authorization_consumed: bool
    authorization_expired: bool
    authorization_reusable: bool
    approved_scope: frozenset[str]
    prohibited_scope: frozenset[str]
    false_keys: frozenset[str]
    parent_authorization_transaction_id: str | None = None
    authorization_consumed_by_task: str | None = None
    authorization_consumed_by_pr: int | None = None
    authorization_consumed_by_feature_commit: str | None = None
    authorization_consumed_by_merge_commit: str | None = None
    implementation_true_keys: frozenset[str] = field(default_factory=frozenset)
    approved_dependency_name: str | None = None
    approved_dependency_specifier: str | None = None
    approved_dependency_manifest: str | None = None
    approved_dependency_change_count: int | None = None

    @property
    def tuple_key(self) -> tuple[str, str, str, str, str]:
        return (
            self.transaction_id,
            self.candidate_id,
            self.workstream,
            self.implementation_task,
            self.authorization_scope,
        )


AION_152_MERGE_COMMIT = "bc0614bcde19448b2a423614836bee3c06728c98"
AION_154_FEATURE_COMMIT = "f001632ed0566bcf7facfe8905a2781ff9fa6ce9"
AION_154_MERGE_COMMIT = "85584ea1976fd6f2cb73a641464b3caf87481618"
AION_156_FEATURE_COMMIT = "2fbeb77bdc33772c46a679cbfa0bdafe327abb42"
AION_156_MERGE_COMMIT = "051f6f2e8b901863f8dc9cad405e5b5401db3695"
AION_158_FEATURE_COMMIT = "767fd9b228b00b04569df2e3b1b3f6bc9ecd846f"
AION_158_MERGE_COMMIT = "f792c92e1d8a73ec8e7377b5d59269dea359006d"
AION_160_FEATURE_COMMIT = "085b1b9d9cbbc23a735c1a82be66a2e901a56761"
AION_160_MERGE_COMMIT = "bfc2afdc96358559027ee36efc0bc26ed3bb796d"
AION_162_PRIMARY_FEATURE_COMMIT = "954bc096847699807b60847f6506ec740e69c971"
AION_162_PRIMARY_MERGE_COMMIT = "33e8d7da6a57ad71aefc1dd20a3126050b3517ff"
AION_162_CORRECTIVE_FEATURE_COMMIT = "9ff614e139cf7f5cb882e969106fac9aa7fa88da"
AION_162_CORRECTIVE_MERGE_COMMIT = "d8a1705028796fb35ffb214e7f56d571e7c66025"
AION_162_FINAL_MAIN_COMMIT = AION_162_CORRECTIVE_MERGE_COMMIT

APPROVAL_TRUE_KEYS = frozenset(
    {
        "authorization_transaction_approved",
        "explicit_approval_record_approval",
        "implementation_authorization_approved",
        "implementation_go_status",
    }
)

LEGACY_FALSE_KEYS = frozenset(
    {
        "implementation_no_go_status",
        "runtime_implementation_approved",
        "production_auth_runtime_enabled",
        "runtime_enablement_guard_release_approved",
        "runtime_enablement_guard_final_lock_release_approved",
        "runtime_enablement_master_lock_release_approved",
        "login_endpoint_approved",
        "logout_endpoint_approved",
        "callback_endpoint_approved",
        "credential_storage_approved",
        "password_storage_approved",
        "token_storage_approved",
        "session_storage_approved",
        "cookie_session_persistence_approved",
        "external_identity_provider_approved",
        "oauth_runtime_approved",
        "oidc_runtime_approved",
        "saml_runtime_approved",
        "external_calls_approved",
        "network_client_approved",
        "provider_sdk_approved",
        "operator_write_execution_approved",
        "connector_implementation_approved",
        "connector_runtime_enabled",
        "module_activation_approved",
        "sandbox_execution_approved",
        "package_files_added",
        "lockfiles_added",
        "migrations_added",
        "runtime_api_routes_added",
        "v02_tag_created",
        "v02_release_created",
        "v02_release_approved",
    }
)

REQUEST_BOUNDARY_FALSE_KEYS = LEGACY_FALSE_KEYS | frozenset(
    {
        "identity_verification_enabled",
        "authenticated_requests_enabled",
        "authorization_header_parsing_approved",
        "cookie_parsing_approved",
        "credential_verification_approved",
        "password_verification_approved",
        "token_parsing_approved",
        "token_issuance_approved",
        "token_refresh_approved",
        "session_creation_approved",
        "cookie_issuance_approved",
        "token_endpoint_approved",
        "session_endpoint_approved",
        "credential_endpoint_approved",
        "openapi_security_scheme_added",
        "sdk_runtime_resource_added",
        "cli_runtime_command_added",
    }
)

REQUEST_IDENTITY_STABILIZATION_FALSE_KEYS = REQUEST_BOUNDARY_FALSE_KEYS | frozenset(
    {
        "password_storage_approved",
        "token_endpoint_approved",
        "session_endpoint_approved",
        "credential_endpoint_approved",
        "openapi_security_scheme_added",
        "sdk_runtime_resource_added",
        "cli_runtime_command_added",
    }
)

ACTOR_CONTEXT_TRUST_BOUNDARY_FALSE_KEYS = REQUEST_IDENTITY_STABILIZATION_FALSE_KEYS | frozenset(
    {
        "authenticated_actor_context_enabled",
        "non_development_identity_header_trust_enabled",
        "production_identity_header_trust_approved",
        "production_actor_header_trust_enabled",
        "production_role_header_trust_enabled",
        "production_permission_header_trust_enabled",
        "production_security_scope_header_trust_enabled",
        "protected_material_handling_approved",
        "provider_runtime_approved",
        "runtime_effect",
    }
)

CANONICAL_FALSE_KEYS = ACTOR_CONTEXT_TRUST_BOUNDARY_FALSE_KEYS

OFFLINE_IDENTITY_ASSERTION_FALSE_KEYS = ACTOR_CONTEXT_TRUST_BOUNDARY_FALSE_KEYS | frozenset(
    {
        "identity_verification_runtime_enabled",
        "identity_assertion_header_parsing_approved",
        "identity_assertion_middleware_registration_approved",
        "request_identity_verifier_replacement_approved",
        "actor_context_resolver_integration_approved",
        "runtime_private_key_material_approved",
        "private_key_configuration_approved",
        "private_key_persistence_approved",
        "private_key_serialization_approved",
        "raw_assertion_logging_approved",
        "verified_claims_logging_approved",
        "verified_claims_persistence_approved",
        "jwks_network_fetch_approved",
        "provider_discovery_approved",
        "replay_cache_approved",
        "replay_protection_runtime_approved",
        "identity_assertion_endpoint_approved",
        "new_package_manifest_added",
        "openapi_security_scheme_added",
        "actor_context_application_approved",
        "request_identity_context_application_approved",
        "runtime_effect_approved",
        "runtime_effect",
    }
)

GLOBAL_FALSE_KEYS = (ACTOR_CONTEXT_TRUST_BOUNDARY_FALSE_KEYS - {"implementation_no_go_status"}) | {
    "runtime_enablement_guard_release_approved",
    "runtime_enablement_master_lock_release_approved",
    "runtime_enablement_guard_final_lock_release_approved",
    "runtime_implementation_approved",
    "production_auth_runtime_enabled",
    "production_auth_enabled",
    "auth_runtime_enabled",
    "identity_verification_enabled",
    "authenticated_requests_enabled",
    "authenticated_actor_context_enabled",
    "non_development_identity_header_trust_enabled",
    "production_identity_header_trust_approved",
    "production_actor_header_trust_enabled",
    "production_role_header_trust_enabled",
    "production_permission_header_trust_enabled",
    "production_security_scope_header_trust_enabled",
    "protected_material_handling_approved",
    "provider_runtime_approved",
    "runtime_effect",
    "authorization_header_parsing_approved",
    "cookie_parsing_approved",
    "credential_verification_approved",
    "password_verification_approved",
    "token_parsing_approved",
    "external_calls_enabled",
    "network_client_enabled",
    "provider_sdk_dependency_added",
    "provider_sdk_enabled",
    "package_manager_file_added",
    "api_runtime_execution_route_added",
    "connector_runtime_enabled",
    "connector_activation_enabled",
    "operator_write_execution_enabled",
    "module_activation_enabled",
    "sandbox_execution_enabled",
    "credentials_present",
    "tokens_present",
    "secrets_present",
    "credential_values_present",
    "token_values_present",
    "login_endpoint_enabled",
    "logout_endpoint_enabled",
    "callback_endpoint_enabled",
    "credential_storage_enabled",
    "password_storage_enabled",
    "password_verification_enabled",
    "token_issuance_enabled",
    "token_storage_enabled",
    "token_refresh_enabled",
    "session_creation_enabled",
    "session_storage_enabled",
    "cookie_issuance_enabled",
    "cookie_session_persistence_enabled",
    "external_identity_provider_enabled",
    "oauth_runtime_enabled",
    "oidc_runtime_enabled",
    "saml_runtime_enabled",
    "identity_verification_runtime_enabled",
    "identity_assertion_header_parsing_approved",
    "identity_assertion_middleware_registration_approved",
    "request_identity_verifier_replacement_approved",
    "actor_context_resolver_integration_approved",
    "runtime_private_key_material_approved",
    "private_key_configuration_approved",
    "private_key_persistence_approved",
    "private_key_serialization_approved",
    "raw_assertion_logging_approved",
    "verified_claims_logging_approved",
    "verified_claims_persistence_approved",
    "jwks_network_fetch_approved",
    "provider_discovery_approved",
    "replay_cache_approved",
    "replay_protection_runtime_approved",
    "replay_protection_core_runtime_enabled",
    "replay_repository_runtime_registered",
    "kernel_container_integration_approved",
    "request_middleware_integration_approved",
    "request_body_parsing_approved",
    "dependency_change_approved",
    "new_dependency_approved",
    "new_package_manifest_approved",
    "lockfile_approved",
    "database_migration_approved",
    "production_schema_auto_create_approved",
    "raw_assertion_persistence_approved",
    "signature_persistence_approved",
    "signature_logging_approved",
    "raw_claim_persistence_approved",
    "verified_claim_persistence_approved",
    "raw_claim_logging_approved",
    "in_memory_runtime_replay_store_approved",
    "background_cleanup_scheduler_approved",
    "automatic_runtime_schema_creation_approved",
    "identity_assertion_endpoint_approved",
    "new_package_manifest_added",
    "request_identity_context_application_approved",
    "actor_context_application_approved",
    "runtime_effect_approved",
}

HISTORICAL_REQUIRED_SCOPE = frozenset(
    {
        "internal production-auth contracts",
        "internal production-auth configuration model",
        "disabled-by-default feature flags",
        "policy evaluation interfaces",
        "audit and provenance events",
        "redacted diagnostics",
        "deterministic test fixtures",
        "unit and integration tests",
        "documentation",
        "read-only static-console status evidence",
    }
)

STABILIZATION_REQUIRED_SCOPE = frozenset(
    {
        "internal production-auth core stabilization",
        "disabled-by-default configuration hardening",
        "fail-closed policy stabilization",
        "audit and provenance evidence stabilization",
        "redacted diagnostics stabilization",
        "deterministic stabilization tests",
        "documentation",
        "read-only static-console status evidence",
    }
)

REQUEST_BOUNDARY_APPROVED_SCOPE = frozenset(
    {
        "request_identity_contracts",
        "provider_agnostic_verifier_interface",
        "disabled_verifier",
        "deterministic_test_verifier",
        "anonymous_disabled_context_attachment",
        "observe_only_boundary_registration",
        "audit_provenance_correlation",
        "read_only_diagnostics",
        "tests",
        "documentation",
    }
)

REQUEST_IDENTITY_STABILIZATION_APPROVED_SCOPE = frozenset(
    {
        "pure_asgi_middleware_migration",
        "middleware_order_hardening",
        "streaming_response_preservation",
        "request_body_preservation",
        "cancellation_propagation",
        "client_disconnect_hardening",
        "non_http_scope_bypass",
        "request_state_integrity",
        "duplicate_registration_guard",
        "concurrency_reentrancy",
        "state_leakage_regression",
        "evidence_idempotency",
        "diagnostic_schema_hardening",
        "performance_smoke",
        "tests",
        "documentation",
    }
)

ACTOR_CONTEXT_TRUST_BOUNDARY_APPROVED_SCOPE = frozenset(
    {
        "actor_context_trust_boundary_remediation",
        "non_development_identity_header_rejection",
        "development_header_simulation_isolation",
        "request_identity_context_precedence",
        "request_context_correlation_projection",
        "anonymous_actor_context_fallback",
        "route_dependency_hardening",
        "privilege_escalation_regression",
        "actor_context_audit_provenance",
        "backward_compatible_dev_simulation",
        "tests",
        "documentation",
    }
)

PROHIBITED_SCOPE = frozenset(
    {
        "runtime enablement",
        "login endpoints",
        "logout endpoints",
        "authentication callback endpoints",
        "credential storage",
        "password storage",
        "token issuance",
        "token storage",
        "cookie or session persistence",
        "database migrations",
        "external identity providers",
        "network calls",
        "OAuth runtime",
        "OIDC runtime",
        "SAML runtime",
        "provider SDK installation",
        "frontend dependencies",
        "package or lockfile changes",
        "operator write execution",
        "connector runtime",
        "module activation",
        "sandbox execution",
        "production release or tag creation",
    }
)

REQUEST_BOUNDARY_PROHIBITED_SCOPE = frozenset(
    {
        "authorization_header_parsing",
        "cookie_parsing",
        "credential_verification",
        "password_verification",
        "token_parsing",
        "token_issuance",
        "token_refresh",
        "token_storage",
        "session_creation",
        "session_persistence",
        "cookie_issuance",
        "cookie_persistence",
        "external_identity_provider",
        "oauth_runtime",
        "oidc_runtime",
        "saml_runtime",
        "external_calls",
        "provider_sdk",
        "login_endpoint",
        "logout_endpoint",
        "callback_endpoint",
        "token_endpoint",
        "session_endpoint",
        "credential_endpoint",
        "migrations",
        "package_files",
        "lockfiles",
        "sdk_runtime_resource",
        "cli_runtime_command",
        "connector_runtime",
        "operator_write_execution",
        "module_activation",
        "sandbox_execution",
        "v02_tag",
        "v02_release",
    }
)

REQUEST_IDENTITY_STABILIZATION_PROHIBITED_SCOPE = frozenset(
    {
        "identity_verification",
        "authenticated_requests",
        "authorization_header_parsing",
        "cookie_parsing",
        "credential_verification",
        "password_verification",
        "token_parsing",
        "token_issuance",
        "token_refresh",
        "token_storage",
        "session_creation",
        "session_persistence",
        "cookie_issuance",
        "cookie_persistence",
        "external_identity_provider",
        "oauth_runtime",
        "oidc_runtime",
        "saml_runtime",
        "external_calls",
        "network_client",
        "provider_sdk",
        "login_endpoint",
        "logout_endpoint",
        "callback_endpoint",
        "token_endpoint",
        "session_endpoint",
        "credential_endpoint",
        "api_router",
        "openapi_security_scheme",
        "package_files",
        "lockfiles",
        "migrations",
        "sdk_runtime_resource",
        "cli_runtime_command",
        "connector_runtime",
        "operator_write_execution",
        "module_activation",
        "sandbox_execution",
        "v02_tag",
        "v02_release",
    }
)

ACTOR_CONTEXT_TRUST_BOUNDARY_PROHIBITED_SCOPE = frozenset(
    {
        "production_identity_header_trust",
        "production_role_header_trust",
        "production_permission_header_trust",
        "production_security_scope_header_trust",
        "identity_verification",
        "authenticated_requests",
        "authorization_header_parsing",
        "cookie_parsing",
        "credential_verification",
        "password_verification",
        "token_parsing",
        "token_issuance",
        "token_refresh",
        "token_storage",
        "session_creation",
        "session_persistence",
        "cookie_issuance",
        "cookie_persistence",
        "protected_material",
        "external_identity_provider",
        "oauth_runtime",
        "oidc_runtime",
        "saml_runtime",
        "external_calls",
        "network_client",
        "provider_sdk",
        "login_endpoint",
        "logout_endpoint",
        "callback_endpoint",
        "token_endpoint",
        "session_endpoint",
        "credential_endpoint",
        "api_router",
        "openapi_security_scheme",
        "package_files",
        "lockfiles",
        "migrations",
        "sdk_runtime_resource",
        "cli_runtime_command",
        "connector_runtime",
        "operator_write_execution",
        "module_activation",
        "sandbox_execution",
        "v02_tag",
        "v02_release",
    }
)

OFFLINE_IDENTITY_ASSERTION_APPROVED_SCOPE = frozenset(
    {
        "identity_assertion_contracts",
        "offline_ed25519_verifier",
        "canonical_signed_payload",
        "signature_domain_separation",
        "static_public_key_registry",
        "multi_public_key_rotation",
        "issuer_validation",
        "audience_validation",
        "temporal_validation",
        "assertion_identifier_validation",
        "claim_constraint_validation",
        "verification_audit_provenance",
        "deterministic_negative_fixtures",
        "test_only_ephemeral_signer",
        "cryptography_dependency_change",
        "tests",
        "documentation",
    }
)

OFFLINE_IDENTITY_ASSERTION_PROHIBITED_SCOPE = frozenset(
    {
        "http_header_parsing",
        "authorization_header_parsing",
        "cookie_parsing",
        "middleware_registration",
        "request_authentication",
        "request_identity_context_application",
        "actor_context_application",
        "runtime_private_key",
        "private_key_configuration",
        "private_key_persistence",
        "private_key_serialization",
        "raw_assertion_logging",
        "verified_claims_logging",
        "verified_claims_persistence",
        "external_identity_provider",
        "oauth_runtime",
        "oidc_runtime",
        "saml_runtime",
        "jwks_network_fetch",
        "provider_discovery",
        "external_calls",
        "network_client",
        "provider_sdk",
        "replay_cache",
        "login_endpoint",
        "logout_endpoint",
        "callback_endpoint",
        "token_endpoint",
        "session_endpoint",
        "credential_endpoint",
        "identity_assertion_endpoint",
        "api_router",
        "openapi_security_scheme",
        "new_package_manifest",
        "lockfiles",
        "migrations",
        "sdk_runtime_resource",
        "cli_runtime_command",
        "connector_runtime",
        "operator_write_execution",
        "module_activation",
        "sandbox_execution",
        "v02_tag",
        "v02_release",
    }
)

REQUEST_BOUNDARY_IMPLEMENTATION_TRUE_KEYS = frozenset(
    {
        "request_identity_boundary_implementation_approved",
        "request_identity_boundary_registration_approved",
        "anonymous_disabled_context_attachment_approved",
        "provider_agnostic_verifier_interface_approved",
        "deterministic_test_verifier_approved",
        "audit_provenance_correlation_approved",
    }
)

REQUEST_IDENTITY_STABILIZATION_TRUE_KEYS = frozenset(
    {
        "request_identity_boundary_stabilization_approved",
        "pure_asgi_middleware_migration_approved",
        "middleware_order_hardening_approved",
        "streaming_response_preservation_approved",
        "request_body_preservation_approved",
        "cancellation_propagation_hardening_approved",
        "client_disconnect_hardening_approved",
        "non_http_scope_bypass_approved",
        "request_state_integrity_hardening_approved",
        "duplicate_registration_guard_approved",
        "concurrency_reentrancy_hardening_approved",
        "state_leakage_regression_approved",
        "evidence_idempotency_hardening_approved",
        "diagnostic_schema_hardening_approved",
        "performance_smoke_hardening_approved",
    }
)

ACTOR_CONTEXT_TRUST_BOUNDARY_TRUE_KEYS = frozenset(
    {
        "actor_context_trust_boundary_remediation_approved",
        "non_development_identity_header_rejection_approved",
        "development_header_simulation_isolation_approved",
        "request_identity_context_precedence_approved",
        "request_context_correlation_projection_approved",
        "anonymous_actor_context_fallback_approved",
        "route_dependency_hardening_approved",
        "privilege_escalation_regression_approved",
        "actor_context_audit_provenance_approved",
        "backward_compatible_dev_simulation_approved",
    }
)

OFFLINE_IDENTITY_ASSERTION_TRUE_KEYS = frozenset(
    {
        "identity_assertion_contracts_approved",
        "offline_identity_assertion_verifier_approved",
        "ed25519_signature_verification_approved",
        "canonical_signed_payload_approved",
        "signature_domain_separation_approved",
        "static_public_key_registry_approved",
        "multi_public_key_rotation_approved",
        "issuer_validation_approved",
        "audience_validation_approved",
        "temporal_claim_validation_approved",
        "assertion_identifier_validation_approved",
        "claim_constraint_validation_approved",
        "verification_audit_provenance_approved",
        "deterministic_negative_fixture_approved",
        "test_only_ephemeral_signer_approved",
        "cryptography_dependency_change_approved",
        "existing_dependency_manifest_change_approved",
    }
)

IDENTITY_ASSERTION_REPLAY_PROTECTION_APPROVED_SCOPE = frozenset(
    {
        "identity_assertion_replay_contracts",
        "domain_separated_replay_key",
        "replay_key_hashing",
        "atomic_replay_claim",
        "persistent_replay_ledger",
        "sqlalchemy_replay_repository",
        "existing_sqlalchemy_dependency_reuse",
        "unique_replay_key_constraint",
        "assertion_fingerprint_binding",
        "assertion_identifier_collision_detection",
        "verification_bundle_binding",
        "repository_failure_fail_closed",
        "retention_policy",
        "explicit_retention_cleanup",
        "concurrency_race_hardening",
        "multiple_repository_instance_regression",
        "internal_offline_verification_pipeline",
        "replay_audit_provenance",
        "safe_diagnostics",
        "test_only_schema_auto_create",
        "performance_smoke",
        "tests",
        "documentation",
    }
)

IDENTITY_ASSERTION_REPLAY_PROTECTION_PROHIBITED_SCOPE = frozenset(
    {
        "dependency_change",
        "new_dependency",
        "new_package_manifest",
        "lockfile",
        "database_migration",
        "production_schema_auto_create",
        "kernel_container_integration",
        "request_middleware_integration",
        "request_identity_verifier_replacement",
        "actor_context_resolver_integration",
        "request_authentication",
        "actor_context_application",
        "request_identity_context_application",
        "http_header_parsing",
        "authorization_header_parsing",
        "cookie_parsing",
        "request_body_parsing",
        "runtime_private_key",
        "raw_assertion_persistence",
        "raw_assertion_logging",
        "signature_persistence",
        "signature_logging",
        "raw_claim_persistence",
        "verified_claim_persistence",
        "in_memory_runtime_replay_store",
        "background_cleanup_scheduler",
        "external_identity_provider",
        "jwks_network_fetch",
        "provider_discovery",
        "external_calls",
        "network_client",
        "provider_sdk",
        "login_endpoint",
        "logout_endpoint",
        "callback_endpoint",
        "token_endpoint",
        "session_endpoint",
        "credential_endpoint",
        "identity_assertion_endpoint",
        "api_router",
        "openapi_security_scheme",
        "sdk_runtime_resource",
        "cli_runtime_command",
        "connector_runtime",
        "operator_write_execution",
        "module_activation",
        "sandbox_execution",
        "v02_tag",
        "v02_release",
    }
)

IDENTITY_ASSERTION_REPLAY_PROTECTION_TRUE_KEYS = frozenset(
    {
        "identity_assertion_replay_contracts_approved",
        "domain_separated_replay_key_approved",
        "replay_key_hashing_approved",
        "atomic_replay_claim_approved",
        "persistent_replay_ledger_approved",
        "sqlalchemy_replay_repository_approved",
        "existing_sqlalchemy_dependency_reuse_approved",
        "unique_replay_key_constraint_approved",
        "assertion_fingerprint_binding_approved",
        "assertion_identifier_collision_detection_approved",
        "verification_bundle_binding_approved",
        "repository_failure_fail_closed_approved",
        "retention_policy_approved",
        "explicit_retention_cleanup_approved",
        "concurrency_race_hardening_approved",
        "multiple_repository_instance_regression_approved",
        "internal_offline_verification_pipeline_approved",
        "replay_audit_provenance_approved",
        "replay_diagnostic_snapshot_approved",
        "safe_diagnostics_approved",
        "deterministic_test_fixture_approved",
        "test_only_schema_auto_create_approved",
        "performance_smoke_approved",
        "database_table_definition_approved",
    }
)

IDENTITY_ASSERTION_REPLAY_PROTECTION_FALSE_KEYS = OFFLINE_IDENTITY_ASSERTION_FALSE_KEYS | frozenset(
    {
        "dependency_change_approved",
        "new_dependency_approved",
        "new_package_manifest_approved",
        "lockfile_approved",
        "database_migration_approved",
        "production_schema_auto_create_approved",
        "replay_protection_core_runtime_enabled",
        "replay_repository_runtime_registered",
        "kernel_container_integration_approved",
        "request_authentication_approved",
        "request_middleware_integration_approved",
        "request_body_parsing_approved",
        "raw_assertion_persistence_approved",
        "signature_persistence_approved",
        "signature_logging_approved",
        "raw_claim_persistence_approved",
        "verified_claim_persistence_approved",
        "raw_claim_logging_approved",
        "in_memory_runtime_replay_store_approved",
        "background_cleanup_scheduler_approved",
        "automatic_runtime_schema_creation_approved",
        "openapi_security_scheme_added",
        "sdk_runtime_resource_added",
        "cli_runtime_command_added",
    }
)

AION151_AUTHORIZATION = AuthorizationSpec(
    transaction_id="AION-151-PA-0001",
    approval_record_id="AION-151-PA-0001",
    candidate_id="production-auth-core",
    workstream="production-auth-implementation",
    implementation_task="AION-152",
    authorization_scope="disabled-production-auth-core",
    task_id="AION-151",
    required_adr="0142-v02-production-auth-implementation-authorization.md",
    expiry="AION-152 merged; authorization consumed by PR 62",
    authorization_active=False,
    authorization_consumed=True,
    authorization_expired=True,
    authorization_reusable=False,
    approved_scope=HISTORICAL_REQUIRED_SCOPE,
    prohibited_scope=PROHIBITED_SCOPE,
    false_keys=LEGACY_FALSE_KEYS,
    authorization_consumed_by_task="AION-152",
    authorization_consumed_by_pr=62,
    authorization_consumed_by_merge_commit=AION_152_MERGE_COMMIT,
)

AION153_AUTHORIZATION = AuthorizationSpec(
    transaction_id="AION-153-PA-0002",
    approval_record_id="AION-153-PA-0002",
    candidate_id="production-auth-core-stabilization",
    workstream="production-auth-hardening",
    implementation_task="AION-154",
    authorization_scope="disabled-production-auth-core-stabilization",
    task_id="AION-153",
    required_adr="0144-v02-production-auth-core-stabilization-authorization.md",
    expiry="AION-154 merged; authorization consumed by PR 64",
    authorization_active=False,
    authorization_consumed=True,
    authorization_expired=True,
    authorization_reusable=False,
    approved_scope=STABILIZATION_REQUIRED_SCOPE,
    prohibited_scope=PROHIBITED_SCOPE,
    false_keys=LEGACY_FALSE_KEYS,
    parent_authorization_transaction_id="AION-151-PA-0001",
    authorization_consumed_by_task="AION-154",
    authorization_consumed_by_pr=64,
    authorization_consumed_by_feature_commit=AION_154_FEATURE_COMMIT,
    authorization_consumed_by_merge_commit=AION_154_MERGE_COMMIT,
)

AION155_AUTHORIZATION = AuthorizationSpec(
    transaction_id="AION-155-PA-0003",
    approval_record_id="AION-155-PA-0003",
    candidate_id="production-auth-request-identity-boundary",
    workstream="production-auth-request-integration",
    implementation_task="AION-156",
    authorization_scope="disabled-request-identity-boundary",
    task_id="AION-155",
    required_adr="0146-v02-production-auth-request-boundary-authorization.md",
    expiry="AION-156 merged; authorization consumed by PR 66",
    authorization_active=False,
    authorization_consumed=True,
    authorization_expired=True,
    authorization_reusable=False,
    approved_scope=REQUEST_BOUNDARY_APPROVED_SCOPE,
    prohibited_scope=REQUEST_BOUNDARY_PROHIBITED_SCOPE,
    false_keys=REQUEST_BOUNDARY_FALSE_KEYS,
    parent_authorization_transaction_id="AION-153-PA-0002",
    authorization_consumed_by_task="AION-156",
    authorization_consumed_by_pr=66,
    authorization_consumed_by_feature_commit=AION_156_FEATURE_COMMIT,
    authorization_consumed_by_merge_commit=AION_156_MERGE_COMMIT,
    implementation_true_keys=REQUEST_BOUNDARY_IMPLEMENTATION_TRUE_KEYS,
)

AION157_AUTHORIZATION = AuthorizationSpec(
    transaction_id="AION-157-PA-0004",
    approval_record_id="AION-157-PA-0004",
    candidate_id="production-auth-request-identity-boundary-stabilization",
    workstream="production-auth-request-integration-hardening",
    implementation_task="AION-158",
    authorization_scope="disabled-request-identity-boundary-stabilization",
    task_id="AION-157",
    required_adr="0148-v02-production-auth-request-identity-stabilization-authorization.md",
    expiry="AION-158 merged; authorization consumed by PR 68",
    authorization_active=False,
    authorization_consumed=True,
    authorization_expired=True,
    authorization_reusable=False,
    approved_scope=REQUEST_IDENTITY_STABILIZATION_APPROVED_SCOPE,
    prohibited_scope=REQUEST_IDENTITY_STABILIZATION_PROHIBITED_SCOPE,
    false_keys=REQUEST_IDENTITY_STABILIZATION_FALSE_KEYS,
    parent_authorization_transaction_id="AION-155-PA-0003",
    authorization_consumed_by_task="AION-158",
    authorization_consumed_by_pr=68,
    authorization_consumed_by_feature_commit=AION_158_FEATURE_COMMIT,
    authorization_consumed_by_merge_commit=AION_158_MERGE_COMMIT,
    implementation_true_keys=REQUEST_IDENTITY_STABILIZATION_TRUE_KEYS,
)

AION159_AUTHORIZATION = AuthorizationSpec(
    transaction_id="AION-159-PA-0005",
    approval_record_id="AION-159-PA-0005",
    candidate_id="production-auth-actor-context-trust-boundary",
    workstream="production-auth-route-context-hardening",
    implementation_task="AION-160",
    authorization_scope="fail-closed-actor-context-resolution",
    task_id="AION-159",
    required_adr="0150-v02-actor-context-trust-boundary-authorization.md",
    expiry="AION-160 merged; authorization consumed by PR 70",
    authorization_active=False,
    authorization_consumed=True,
    authorization_expired=True,
    authorization_reusable=False,
    approved_scope=ACTOR_CONTEXT_TRUST_BOUNDARY_APPROVED_SCOPE,
    prohibited_scope=ACTOR_CONTEXT_TRUST_BOUNDARY_PROHIBITED_SCOPE,
    false_keys=ACTOR_CONTEXT_TRUST_BOUNDARY_FALSE_KEYS,
    parent_authorization_transaction_id="AION-157-PA-0004",
    authorization_consumed_by_task="AION-160",
    authorization_consumed_by_pr=70,
    authorization_consumed_by_feature_commit=AION_160_FEATURE_COMMIT,
    authorization_consumed_by_merge_commit=AION_160_MERGE_COMMIT,
    implementation_true_keys=ACTOR_CONTEXT_TRUST_BOUNDARY_TRUE_KEYS,
)

AION161_AUTHORIZATION = AuthorizationSpec(
    transaction_id="AION-161-PA-0006",
    approval_record_id="AION-161-PA-0006",
    candidate_id="production-auth-offline-identity-assertion-verification",
    workstream="production-auth-verification-core",
    implementation_task="AION-162",
    authorization_scope="offline-ed25519-identity-assertion-verification",
    task_id="AION-161",
    required_adr="0152-v02-offline-ed25519-identity-assertion-verification-authorization.md",
    expiry="AION-162 merged through PR 72 and post-merge PR 73; authorization consumed",
    authorization_active=False,
    authorization_consumed=True,
    authorization_expired=True,
    authorization_reusable=False,
    approved_scope=OFFLINE_IDENTITY_ASSERTION_APPROVED_SCOPE,
    prohibited_scope=OFFLINE_IDENTITY_ASSERTION_PROHIBITED_SCOPE,
    false_keys=OFFLINE_IDENTITY_ASSERTION_FALSE_KEYS,
    parent_authorization_transaction_id="AION-159-PA-0005",
    authorization_consumed_by_task="AION-162",
    authorization_consumed_by_pr=72,
    authorization_consumed_by_feature_commit=AION_162_PRIMARY_FEATURE_COMMIT,
    authorization_consumed_by_merge_commit=AION_162_PRIMARY_MERGE_COMMIT,
    implementation_true_keys=OFFLINE_IDENTITY_ASSERTION_TRUE_KEYS,
    approved_dependency_name="cryptography",
    approved_dependency_specifier=">=49.0.0,<50.0.0",
    approved_dependency_manifest="services/brain-api/pyproject.toml",
    approved_dependency_change_count=1,
)

AION163_AUTHORIZATION = AuthorizationSpec(
    transaction_id="AION-163-PA-0007",
    approval_record_id="AION-163-PA-0007",
    candidate_id="production-auth-identity-assertion-replay-protection",
    workstream="production-auth-verification-integrity",
    implementation_task="AION-164",
    authorization_scope="persistent-identity-assertion-replay-protection-core",
    task_id="AION-163",
    required_adr="0154-v02-identity-assertion-replay-protection-authorization.md",
    expiry="AION-164 merged, or AION-163-PA-0007 explicitly revoked",
    authorization_active=True,
    authorization_consumed=False,
    authorization_expired=False,
    authorization_reusable=False,
    approved_scope=IDENTITY_ASSERTION_REPLAY_PROTECTION_APPROVED_SCOPE,
    prohibited_scope=IDENTITY_ASSERTION_REPLAY_PROTECTION_PROHIBITED_SCOPE,
    false_keys=IDENTITY_ASSERTION_REPLAY_PROTECTION_FALSE_KEYS,
    parent_authorization_transaction_id="AION-161-PA-0006",
    implementation_true_keys=IDENTITY_ASSERTION_REPLAY_PROTECTION_TRUE_KEYS,
)

HISTORICAL_AUTHORIZATION = AION151_AUTHORIZATION
STABILIZATION_AUTHORIZATION = AION153_AUTHORIZATION
ACTIVE_AUTHORIZATION = AION163_AUTHORIZATION
ACTIVE_REQUIRED_SCOPE = IDENTITY_ASSERTION_REPLAY_PROTECTION_APPROVED_SCOPE

AUTHORIZATION_SPECS = {
    spec.transaction_id: spec
    for spec in (
        AION151_AUTHORIZATION,
        AION153_AUTHORIZATION,
        AION155_AUTHORIZATION,
        AION157_AUTHORIZATION,
        AION159_AUTHORIZATION,
        AION161_AUTHORIZATION,
        AION163_AUTHORIZATION,
    )
}

REQUIRED_DOCS_AION151 = [
    "docs/release/v02-production-auth-implementation-authorization-transaction.md",
    "docs/release/v02-production-auth-explicit-approval-record.md",
    "docs/release/v02-production-auth-implementation-scope.md",
    "docs/release/v02-production-auth-runtime-guard-hold.md",
    "docs/release/v02-production-auth-authorization-evidence-matrix.md",
    "docs/release/v02-production-auth-authorization-no-go.md",
    "docs/release/v02-production-auth-authorization-checklist.md",
    "docs/adr/0142-v02-production-auth-implementation-authorization.md",
]

REQUIRED_JSON_AION151 = [
    "examples/release/v02-production-auth-implementation-authorization.json",
    "examples/release/v02-production-auth-explicit-approval-record.json",
    "examples/release/v02-production-auth-runtime-guard-hold.json",
    "examples/release/v02-production-auth-authorization-evidence-matrix.json",
    "operator-console-static/demo-data/v02-production-auth-authorization.json",
    "operator-console-static/demo-data/v02-production-auth-runtime-guard-hold.json",
]

REQUIRED_DOCS_AION153 = [
    "docs/release/v02-production-auth-core-implementation-closeout.md",
    "docs/release/v02-production-auth-stabilization-authorization-transaction.md",
    "docs/release/v02-production-auth-stabilization-explicit-approval-record.md",
    "docs/release/v02-production-auth-stabilization-scope.md",
    "docs/release/v02-production-auth-stabilization-runtime-guard-renewal.md",
    "docs/release/v02-production-auth-stabilization-authorization-evidence-matrix.md",
    "docs/release/v02-production-auth-stabilization-authorization-no-go.md",
    "docs/release/v02-production-auth-stabilization-authorization-checklist.md",
    "docs/adr/0144-v02-production-auth-core-stabilization-authorization.md",
]

REQUIRED_JSON_AION153 = [
    "examples/release/v02-production-auth-stabilization-authorization.json",
    "examples/release/v02-production-auth-stabilization-explicit-approval-record.json",
    "examples/release/v02-production-auth-stabilization-runtime-guard-renewal.json",
    "examples/release/v02-production-auth-stabilization-authorization-evidence-matrix.json",
    "operator-console-static/demo-data/v02-production-auth-stabilization-authorization.json",
]

REQUIRED_JSON_AION153_CLOSEOUT = [
    "examples/release/v02-production-auth-core-implementation-closeout.json",
    "operator-console-static/demo-data/v02-production-auth-core-implementation-closeout.json",
]

REQUIRED_DOCS_AION155 = [
    "docs/project-status.md",
    "docs/release/v02-production-auth-core-stabilization-closeout.md",
    "docs/release/v02-production-auth-request-boundary-authorization-transaction.md",
    "docs/release/v02-production-auth-request-boundary-scope.md",
    "docs/release/v02-production-auth-request-boundary-runtime-hold.md",
    "docs/release/v02-production-auth-request-boundary-authorization-checklist.md",
    "docs/release/v02-release-readiness-delta.md",
    "docs/adr/0146-v02-production-auth-request-boundary-authorization.md",
]

REQUIRED_JSON_AION155_CLOSEOUT = [
    "examples/release/v02-production-auth-core-stabilization-closeout.json",
]

REQUIRED_JSON_AION155 = [
    "examples/release/v02-production-auth-request-boundary-authorization.json",
    "examples/release/v02-production-auth-request-boundary-runtime-hold.json",
    "operator-console-static/demo-data/v02-production-auth-request-boundary-authorization.json",
]

REQUIRED_DOCS_AION157 = [
    "docs/release/v02-production-auth-request-identity-boundary-closeout.md",
    "docs/release/v02-production-auth-request-identity-stabilization-authorization-transaction.md",
    "docs/release/v02-production-auth-request-identity-stabilization-explicit-approval-record.md",
    "docs/release/v02-production-auth-request-identity-stabilization-scope.md",
    "docs/release/v02-production-auth-request-identity-stabilization-runtime-guard-renewal.md",
    "docs/release/v02-production-auth-request-identity-stabilization-evidence-matrix.md",
    "docs/release/v02-production-auth-request-identity-stabilization-no-go.md",
    "docs/release/v02-production-auth-request-identity-stabilization-checklist.md",
    "docs/adr/0148-v02-production-auth-request-identity-stabilization-authorization.md",
]

REQUIRED_JSON_AION157_CLOSEOUT = [
    "examples/release/v02-production-auth-request-identity-boundary-closeout.json",
]

REQUIRED_JSON_AION157 = [
    "examples/release/v02-production-auth-request-identity-stabilization-authorization.json",
    "examples/release/v02-production-auth-request-identity-stabilization-explicit-approval-record.json",
    "examples/release/v02-production-auth-request-identity-stabilization-runtime-guard-renewal.json",
    "examples/release/v02-production-auth-request-identity-stabilization-evidence-matrix.json",
    "operator-console-static/demo-data/v02-production-auth-request-identity-stabilization-authorization.json",
]

REQUIRED_DOCS_AION159 = [
    "docs/release/v02-request-identity-stabilization-closeout.md",
    "docs/release/v02-actor-context-trust-boundary-authorization-transaction.md",
    "docs/release/v02-actor-context-trust-boundary-explicit-approval-record.md",
    "docs/release/v02-actor-context-trust-boundary-scope.md",
    "docs/release/v02-actor-context-trust-boundary-runtime-hold.md",
    "docs/release/v02-actor-context-trust-boundary-evidence-matrix.md",
    "docs/release/v02-actor-context-trust-boundary-no-go.md",
    "docs/release/v02-actor-context-trust-boundary-checklist.md",
    "docs/adr/0150-v02-actor-context-trust-boundary-authorization.md",
]

REQUIRED_JSON_AION159_CLOSEOUT = [
    "examples/release/v02-request-identity-stabilization-closeout.json",
]

REQUIRED_JSON_AION159 = [
    "examples/release/v02-actor-context-trust-boundary-authorization.json",
    "examples/release/v02-actor-context-trust-boundary-explicit-approval-record.json",
    "examples/release/v02-actor-context-trust-boundary-runtime-hold.json",
    "examples/release/v02-actor-context-trust-boundary-evidence-matrix.json",
    "operator-console-static/demo-data/v02-actor-context-trust-boundary-authorization.json",
]

REQUIRED_DOCS_AION161 = [
    "docs/release/v02-actor-context-trust-boundary-remediation-closeout.md",
    "docs/release/v02-offline-identity-assertion-verification-authorization-transaction.md",
    "docs/release/v02-offline-identity-assertion-verification-explicit-approval-record.md",
    "docs/release/v02-offline-identity-assertion-verification-scope.md",
    "docs/release/v02-offline-identity-assertion-verification-threat-model.md",
    "docs/release/v02-offline-identity-assertion-verification-runtime-hold.md",
    "docs/release/v02-offline-identity-assertion-verification-evidence-matrix.md",
    "docs/release/v02-offline-identity-assertion-verification-no-go.md",
    "docs/release/v02-offline-identity-assertion-verification-checklist.md",
    "docs/adr/0152-v02-offline-ed25519-identity-assertion-verification-authorization.md",
]

REQUIRED_JSON_AION161_CLOSEOUT = [
    "examples/release/v02-actor-context-trust-boundary-remediation-closeout.json",
]

REQUIRED_JSON_AION161 = [
    "examples/release/v02-offline-identity-assertion-verification-authorization.json",
    "examples/release/v02-offline-identity-assertion-verification-explicit-approval-record.json",
    "examples/release/v02-offline-identity-assertion-verification-runtime-hold.json",
    "examples/release/v02-offline-identity-assertion-verification-evidence-matrix.json",
    "operator-console-static/demo-data/v02-offline-identity-assertion-verification-authorization.json",
]

REQUIRED_DOCS_AION163 = [
    "docs/release/v02-offline-identity-assertion-verification-closeout.md",
    "docs/release/v02-identity-assertion-replay-protection-authorization-transaction.md",
    "docs/release/v02-identity-assertion-replay-protection-explicit-approval-record.md",
    "docs/release/v02-identity-assertion-replay-protection-scope.md",
    "docs/release/v02-identity-assertion-replay-protection-persistence-model.md",
    "docs/release/v02-identity-assertion-replay-protection-threat-model.md",
    "docs/release/v02-identity-assertion-replay-protection-runtime-hold.md",
    "docs/release/v02-identity-assertion-replay-protection-evidence-matrix.md",
    "docs/release/v02-identity-assertion-replay-protection-no-go.md",
    "docs/release/v02-identity-assertion-replay-protection-checklist.md",
    "docs/adr/0154-v02-identity-assertion-replay-protection-authorization.md",
]

REQUIRED_JSON_AION163_CLOSEOUT = [
    "examples/release/v02-offline-identity-assertion-verification-closeout.json",
]

REQUIRED_JSON_AION163 = [
    "examples/release/v02-identity-assertion-replay-protection-authorization.json",
    "examples/release/v02-identity-assertion-replay-protection-explicit-approval-record.json",
    "examples/release/v02-identity-assertion-replay-protection-runtime-hold.json",
    "examples/release/v02-identity-assertion-replay-protection-evidence-matrix.json",
    "operator-console-static/demo-data/v02-identity-assertion-replay-protection-authorization.json",
]

SAFE_POLICY_MARKER_VALUES = frozenset(
    {
        "runtime_private_key",
        "private_key_configuration",
        "private_key_persistence",
        "private_key_serialization",
    }
)

BLOCKED_VALUE_MARKERS = (
    "http://",
    "https://",
    "sk-",
    "ghp_",
    "xoxb-",
    "-----BEGIN PRIVATE KEY-----",
    "bearer ",
    "basic ",
    "api_key",
    "private_key",
    "client_secret",
    "access_token_value",
    "refresh_token_value",
    "id_token_value",
    "raw_prompt",
    "hidden_reasoning",
    "chain_of_thought",
)

NON_PRODUCTION_AUTH_APPROVAL_RECORDS = frozenset(
    {
        "operator-console-static/demo-data/knowledge-intelligence-source-registry-authorization.json",
        "operator-console-static/demo-data/knowledge-intelligence-claim-graph-authorization.json",
    }
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--mode", choices={"check", "no-go", "guard"}, default="check")
    args = parser.parse_args()
    root = args.repo_root.resolve()

    try:
        validate(root, args.mode)
    except AssertionError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


def validate(root: Path, mode: str) -> None:
    required_paths = (
        REQUIRED_DOCS_AION151
        + REQUIRED_JSON_AION151
        + REQUIRED_DOCS_AION153
        + REQUIRED_JSON_AION153
        + REQUIRED_JSON_AION153_CLOSEOUT
        + REQUIRED_DOCS_AION155
        + REQUIRED_JSON_AION155_CLOSEOUT
        + REQUIRED_JSON_AION155
        + REQUIRED_DOCS_AION157
        + REQUIRED_JSON_AION157_CLOSEOUT
        + REQUIRED_JSON_AION157
        + REQUIRED_DOCS_AION159
        + REQUIRED_JSON_AION159_CLOSEOUT
        + REQUIRED_JSON_AION159
        + REQUIRED_DOCS_AION161
        + REQUIRED_JSON_AION161_CLOSEOUT
        + REQUIRED_JSON_AION161
        + REQUIRED_DOCS_AION163
        + REQUIRED_JSON_AION163_CLOSEOUT
        + REQUIRED_JSON_AION163
    )
    for relative in required_paths:
        assert (root / relative).exists(), f"missing production-auth authorization artifact: {relative}"

    adr_index = (root / "docs/adr/README.md").read_text()
    assert "0142-v02-production-auth-implementation-authorization.md" in adr_index, (
        "ADR 0142 is not indexed"
    )
    assert "0144-v02-production-auth-core-stabilization-authorization.md" in adr_index, (
        "ADR 0144 is not indexed"
    )
    assert "0146-v02-production-auth-request-boundary-authorization.md" in adr_index, (
        "ADR 0146 is not indexed"
    )
    assert "0148-v02-production-auth-request-identity-stabilization-authorization.md" in adr_index, (
        "ADR 0148 is not indexed"
    )
    assert "0150-v02-actor-context-trust-boundary-authorization.md" in adr_index, (
        "ADR 0150 is not indexed"
    )
    assert "0152-v02-offline-ed25519-identity-assertion-verification-authorization.md" in adr_index, (
        "ADR 0152 is not indexed"
    )
    assert "0154-v02-identity-assertion-replay-protection-authorization.md" in adr_index, (
        "ADR 0154 is not indexed"
    )

    for relative in (
        REQUIRED_JSON_AION151
        + REQUIRED_JSON_AION153
        + REQUIRED_JSON_AION153_CLOSEOUT
        + REQUIRED_JSON_AION155_CLOSEOUT
        + REQUIRED_JSON_AION155
        + REQUIRED_JSON_AION157_CLOSEOUT
        + REQUIRED_JSON_AION157
        + REQUIRED_JSON_AION159_CLOSEOUT
        + REQUIRED_JSON_AION159
        + REQUIRED_JSON_AION161_CLOSEOUT
        + REQUIRED_JSON_AION161
        + REQUIRED_JSON_AION163_CLOSEOUT
        + REQUIRED_JSON_AION163
    ):
        validate_required_payload(relative, load_json(root / relative))

    validate_authorization_lifecycle_payloads(iter_json_payloads(root))

    if mode == "guard":
        for relative in (
            REQUIRED_JSON_AION151
            + REQUIRED_JSON_AION153
            + REQUIRED_JSON_AION155
            + REQUIRED_JSON_AION157
            + REQUIRED_JSON_AION159
            + REQUIRED_JSON_AION161
            + REQUIRED_JSON_AION163
        ):
            payload = load_json(root / relative)
            assert payload.get("runtime_guard_hold_active") is True, (
                f"{relative}: runtime_guard_hold_active must be true"
            )
            assert payload.get("runtime_no_go_status") is True, (
                f"{relative}: runtime_no_go_status must be true"
            )
            assert payload.get("production_auth_runtime_enabled") is False, (
                f"{relative}: production_auth_runtime_enabled must be false"
            )

    assert_no_forbidden_file_classes(root)


def validate_required_payload(relative: str, payload: dict[str, Any]) -> None:
    assert payload.get("synthetic") is True, f"{relative}: synthetic must be true"
    assert payload.get("read_only") is True, f"{relative}: read_only must be true"
    assert payload.get("record_kind"), f"{relative}: record_kind missing"

    if relative in REQUIRED_JSON_AION151:
        validate_authorization_record(relative, payload, expected=AION151_AUTHORIZATION)
    elif relative in REQUIRED_JSON_AION153_CLOSEOUT:
        assert payload.get("task_id") == "AION-153", f"{relative}: task_id must be AION-153"
        consumed = payload.get("consumed_authorization_record")
        assert isinstance(consumed, dict), f"{relative}: consumed authorization record missing"
        validate_authorization_record(
            f"{relative}:consumed_authorization_record",
            consumed,
            expected=AION151_AUTHORIZATION,
        )
    elif relative in REQUIRED_JSON_AION153:
        validate_authorization_record(relative, payload, expected=AION153_AUTHORIZATION)
    elif relative in REQUIRED_JSON_AION155_CLOSEOUT:
        validate_aion154_closeout_payload(relative, payload)
    elif relative in REQUIRED_JSON_AION157_CLOSEOUT:
        validate_aion156_closeout_payload(relative, payload)
    elif relative in REQUIRED_JSON_AION157:
        validate_authorization_record(relative, payload, expected=AION157_AUTHORIZATION)
    elif relative in REQUIRED_JSON_AION159_CLOSEOUT:
        validate_aion158_closeout_payload(relative, payload)
    elif relative in REQUIRED_JSON_AION159:
        validate_authorization_record(relative, payload, expected=AION159_AUTHORIZATION)
    elif relative in REQUIRED_JSON_AION161_CLOSEOUT:
        validate_aion160_closeout_payload(relative, payload)
    elif relative in REQUIRED_JSON_AION161:
        validate_authorization_record(relative, payload, expected=AION161_AUTHORIZATION)
    elif relative in REQUIRED_JSON_AION163_CLOSEOUT:
        validate_aion162_closeout_payload(relative, payload)
    elif relative in REQUIRED_JSON_AION163:
        validate_authorization_record(relative, payload, expected=AION163_AUTHORIZATION)
    else:
        validate_authorization_record(relative, payload, expected=AION155_AUTHORIZATION)


def validate_aion154_closeout_payload(relative: str, payload: dict[str, Any]) -> None:
    assert payload.get("task_id") == "AION-155", f"{relative}: task_id must be AION-155"
    assert payload.get("record_kind") == "production_auth_core_stabilization_closeout", (
        f"{relative}: record_kind mismatch"
    )
    required = {
        "authorization_transaction_id": "AION-153-PA-0002",
        "authorization_active": False,
        "authorization_consumed": True,
        "authorization_consumed_by_task": "AION-154",
        "authorization_consumed_by_pr": 64,
        "authorization_consumed_by_feature_commit": AION_154_FEATURE_COMMIT,
        "authorization_consumed_by_merge_commit": AION_154_MERGE_COMMIT,
        "authorization_expired": True,
        "authorization_reusable": False,
        "production_auth_core_state": "implemented_disabled",
        "production_auth_runtime_enabled": False,
        "runtime_no_go_status": True,
    }
    for key, expected in required.items():
        assert payload.get(key) == expected, f"{relative}: {key} mismatch"


def validate_aion156_closeout_payload(relative: str, payload: dict[str, Any]) -> None:
    assert payload.get("task_id") == "AION-157", f"{relative}: task_id must be AION-157"
    assert payload.get("record_kind") == "request_identity_boundary_closeout", (
        f"{relative}: record_kind mismatch"
    )
    required = {
        "authorization_transaction_id": "AION-155-PA-0003",
        "authorization_active": False,
        "authorization_consumed": True,
        "authorization_consumed_by_task": "AION-156",
        "authorization_consumed_by_pr": 66,
        "authorization_consumed_by_feature_commit": AION_156_FEATURE_COMMIT,
        "authorization_consumed_by_merge_commit": AION_156_MERGE_COMMIT,
        "authorization_expired": True,
        "authorization_reusable": False,
        "request_identity_boundary_implemented": True,
        "request_identity_boundary_state": "implemented_disabled",
        "request_identity_boundary_default_enabled": False,
        "request_identity_boundary_mode": "observe_only_disabled",
        "authentication_state": "disabled",
        "authenticated": False,
        "actor_id": None,
        "subject": None,
        "roles": [],
        "runtime_effect": False,
    }
    for key, expected in required.items():
        assert payload.get(key) == expected, f"{relative}: {key} mismatch"


def validate_aion158_closeout_payload(relative: str, payload: dict[str, Any]) -> None:
    assert payload.get("task_id") == "AION-159", f"{relative}: task_id must be AION-159"
    assert payload.get("record_kind") == "request_identity_stabilization_closeout", (
        f"{relative}: record_kind mismatch"
    )
    required = {
        "authorization_transaction_id": "AION-157-PA-0004",
        "authorization_active": False,
        "authorization_consumed": True,
        "authorization_consumed_by_task": "AION-158",
        "authorization_consumed_by_pr": 68,
        "authorization_consumed_by_feature_commit": AION_158_FEATURE_COMMIT,
        "authorization_consumed_by_merge_commit": AION_158_MERGE_COMMIT,
        "authorization_expired": True,
        "authorization_reusable": False,
        "request_identity_middleware_implementation": "pure_asgi",
        "request_identity_boundary_state": "implemented_disabled",
        "identity_verification_enabled": False,
        "authenticated_requests_enabled": False,
        "production_auth_runtime_enabled": False,
    }
    for key, expected in required.items():
        assert payload.get(key) == expected, f"{relative}: {key} mismatch"


def validate_aion160_closeout_payload(relative: str, payload: dict[str, Any]) -> None:
    assert payload.get("task_id") == "AION-161", f"{relative}: task_id must be AION-161"
    assert payload.get("record_kind") == "actor_context_trust_boundary_remediation_closeout", (
        f"{relative}: record_kind mismatch"
    )
    required = {
        "authorization_transaction_id": "AION-159-PA-0005",
        "authorization_active": False,
        "authorization_consumed": True,
        "authorization_consumed_by_task": "AION-160",
        "authorization_consumed_by_pr": 70,
        "authorization_consumed_by_feature_commit": AION_160_FEATURE_COMMIT,
        "authorization_consumed_by_merge_commit": AION_160_MERGE_COMMIT,
        "authorization_expired": True,
        "authorization_reusable": False,
        "actor_context_trust_boundary_remediated": True,
        "actor_context_resolution_state": "implemented_fail_closed",
        "non_development_identity_headers_ignored": True,
        "authenticated_actor_context_enabled": False,
        "production_auth_runtime_enabled": False,
    }
    for key, expected in required.items():
        assert payload.get(key) == expected, f"{relative}: {key} mismatch"


def validate_aion162_closeout_payload(relative: str, payload: dict[str, Any]) -> None:
    assert payload.get("task_id") == "AION-163", f"{relative}: task_id must be AION-163"
    assert payload.get("record_kind") == "offline_identity_assertion_verification_closeout", (
        f"{relative}: record_kind mismatch"
    )
    required = {
        "authorization_transaction_id": "AION-161-PA-0006",
        "authorization_active": False,
        "authorization_consumed": True,
        "authorization_consumed_by_task": "AION-162",
        "authorization_consumed_by_primary_pr": 72,
        "authorization_consumed_by_primary_feature_commit": AION_162_PRIMARY_FEATURE_COMMIT,
        "authorization_consumed_by_primary_merge_commit": AION_162_PRIMARY_MERGE_COMMIT,
        "authorization_post_merge_correction_pr": 73,
        "authorization_post_merge_correction_feature_commit": AION_162_CORRECTIVE_FEATURE_COMMIT,
        "authorization_post_merge_correction_merge_commit": AION_162_CORRECTIVE_MERGE_COMMIT,
        "authorization_final_verified_main_commit": AION_162_FINAL_MAIN_COMMIT,
        "authorization_expired": True,
        "authorization_reusable": False,
        "offline_identity_assertion_verification_implemented": True,
        "offline_identity_assertion_verification_state": "implemented_unintegrated",
        "cryptography_dependency_present": True,
        "cryptography_dependency_specifier": ">=49.0.0,<50.0.0",
        "cryptography_dependency_count": 1,
        "request_authenticated": False,
        "actor_context_applied": False,
        "request_identity_context_applied": False,
        "runtime_effect": False,
        "replay_check_performed": False,
        "replay_protection_required_before_request_integration": True,
        "runtime_private_key_material_present": False,
        "production_auth_runtime_enabled": False,
        "runtime_no_go_status": True,
    }
    for key, expected in required.items():
        assert payload.get(key) == expected, f"{relative}: {key} mismatch"


def validate_authorization_lifecycle_payloads(payloads: list[tuple[str, Any]]) -> None:
    approved_records: dict[tuple[str, str, str, str, str], set[str]] = {}
    active_records: dict[tuple[str, str, str, str, str], set[str]] = {}
    historical_records: dict[tuple[str, str, str, str, str], set[str]] = {}

    for relative, payload in payloads:
        collect_approval_record(relative, payload, approved_records, active_records, historical_records)
        assert_global_false(relative, payload)
        assert_no_blocked_values(relative, payload)

    expected_records = {spec.tuple_key for spec in AUTHORIZATION_SPECS.values()}
    assert set(approved_records) == expected_records, (
        f"unexpected approved authorization records: {sorted(approved_records)}"
    )
    assert set(active_records) == {AION163_AUTHORIZATION.tuple_key}, (
        f"unexpected active approved authorization records: {sorted(active_records)}"
    )
    for spec in (
        AION151_AUTHORIZATION,
        AION153_AUTHORIZATION,
        AION155_AUTHORIZATION,
        AION157_AUTHORIZATION,
        AION159_AUTHORIZATION,
        AION161_AUTHORIZATION,
    ):
        assert spec.tuple_key in historical_records, (
            f"{spec.transaction_id} historical authorization record missing"
        )


def validate_authorization_record(
    relative: str,
    payload: dict[str, Any],
    *,
    expected: AuthorizationSpec | None = None,
) -> AuthorizationSpec:
    true_keys = {key for key in APPROVAL_TRUE_KEYS if payload.get(key) is True}
    assert true_keys == APPROVAL_TRUE_KEYS, f"{relative}: partial authorization approval true keys"

    transaction_id = payload.get("authorization_transaction_id")
    assert isinstance(transaction_id, str), f"{relative}: authorization_transaction_id missing"
    spec = expected or AUTHORIZATION_SPECS.get(transaction_id)
    assert spec is not None, f"{relative}: unknown approved authorization record {transaction_id}"
    assert transaction_id == spec.transaction_id, f"{relative}: authorization_transaction_id mismatch"
    assert payload.get("approval_record_id") == spec.approval_record_id, (
        f"{relative}: approval_record_id mismatch"
    )
    assert payload.get("candidate_id") == spec.candidate_id, f"{relative}: candidate_id mismatch"
    assert payload.get("workstream") == spec.workstream, f"{relative}: workstream mismatch"
    assert payload.get("implementation_task") == spec.implementation_task, (
        f"{relative}: implementation_task mismatch"
    )
    assert payload.get("authorization_scope") == spec.authorization_scope, (
        f"{relative}: authorization_scope mismatch"
    )
    assert payload.get("task_id") == spec.task_id, f"{relative}: task_id mismatch"

    for key in spec.false_keys:
        assert payload.get(key) is False, f"{relative}: {key} must be false"
    for key in spec.implementation_true_keys:
        assert payload.get(key) is True, f"{relative}: {key} must be true"

    allowed_true_permission_keys = APPROVAL_TRUE_KEYS | spec.implementation_true_keys
    actual_true_permission_keys = {
        key
        for key, value in payload.items()
        if value is True
        and (key.endswith("_approved") or key.endswith("_approval") or key == "implementation_go_status")
    }
    assert actual_true_permission_keys == allowed_true_permission_keys, (
        f"{relative}: approved permission set mismatch"
    )

    assert payload.get("runtime_guard_hold_active") is True, (
        f"{relative}: runtime_guard_hold_active must be true"
    )
    assert payload.get("runtime_no_go_status") is True, (
        f"{relative}: runtime_no_go_status must be true"
    )

    assert payload.get("authorization_active") is spec.authorization_active, (
        f"{relative}: authorization_active must be {str(spec.authorization_active).lower()}"
    )
    assert payload.get("authorization_consumed") is spec.authorization_consumed, (
        f"{relative}: authorization_consumed must be {str(spec.authorization_consumed).lower()}"
    )
    assert payload.get("authorization_expired") is spec.authorization_expired, (
        f"{relative}: authorization_expired must be {str(spec.authorization_expired).lower()}"
    )
    assert payload.get("authorization_reusable") is spec.authorization_reusable, (
        f"{relative}: authorization_reusable must be {str(spec.authorization_reusable).lower()}"
    )
    assert payload.get("parent_authorization_transaction_id") == spec.parent_authorization_transaction_id, (
        f"{relative}: parent_authorization_transaction_id mismatch"
    )

    if spec.authorization_consumed:
        assert payload.get("authorization_consumed_by_task") == spec.authorization_consumed_by_task, (
            f"{relative}: authorization_consumed_by_task mismatch"
        )
        assert payload.get("authorization_consumed_by_pr") == spec.authorization_consumed_by_pr, (
            f"{relative}: authorization_consumed_by_pr mismatch"
        )
        if spec.authorization_consumed_by_feature_commit is not None:
            assert (
                payload.get("authorization_consumed_by_feature_commit")
                == spec.authorization_consumed_by_feature_commit
            ), f"{relative}: authorization_consumed_by_feature_commit mismatch"
        assert (
            payload.get("authorization_consumed_by_merge_commit")
            == spec.authorization_consumed_by_merge_commit
        ), f"{relative}: authorization_consumed_by_merge_commit mismatch"
        if (
            spec is AION161_AUTHORIZATION
            and payload.get("record_kind") != "unit_test_authorization_record"
        ):
            assert payload.get("authorization_consumed_by_primary_pr") == 72, (
                f"{relative}: authorization_consumed_by_primary_pr mismatch"
            )
            assert payload.get("authorization_consumed_by_primary_feature_commit") == (
                AION_162_PRIMARY_FEATURE_COMMIT
            ), f"{relative}: authorization_consumed_by_primary_feature_commit mismatch"
            assert payload.get("authorization_consumed_by_primary_merge_commit") == (
                AION_162_PRIMARY_MERGE_COMMIT
            ), f"{relative}: authorization_consumed_by_primary_merge_commit mismatch"
            assert payload.get("authorization_post_merge_correction_pr") == 73, (
                f"{relative}: authorization_post_merge_correction_pr mismatch"
            )
            assert payload.get("authorization_post_merge_correction_feature_commit") == (
                AION_162_CORRECTIVE_FEATURE_COMMIT
            ), f"{relative}: authorization_post_merge_correction_feature_commit mismatch"
            assert payload.get("authorization_post_merge_correction_merge_commit") == (
                AION_162_CORRECTIVE_MERGE_COMMIT
            ), f"{relative}: authorization_post_merge_correction_merge_commit mismatch"
            assert payload.get("authorization_final_verified_main_commit") == AION_162_FINAL_MAIN_COMMIT, (
                f"{relative}: authorization_final_verified_main_commit mismatch"
            )
    else:
        assert payload.get("authorization_consumed_by_task") in {None, ""}, (
            f"{relative}: active authorization must not be consumed by task"
        )
        assert payload.get("authorization_consumed_by_pr") in {None, ""}, (
            f"{relative}: active authorization must not be consumed by PR"
        )
        assert payload.get("authorization_consumed_by_feature_commit") in {None, ""}, (
            f"{relative}: active authorization must not be consumed by feature commit"
        )
        assert payload.get("authorization_consumed_by_merge_commit") in {None, ""}, (
            f"{relative}: active authorization must not be consumed by merge commit"
        )

    assert set(payload.get("approved_scope", [])) == spec.approved_scope, (
        f"{relative}: approved_scope mismatch"
    )
    assert set(payload.get("prohibited_scope", [])) == spec.prohibited_scope, (
        f"{relative}: prohibited_scope mismatch"
    )
    if spec.approved_dependency_name is not None:
        dependency = payload.get("approved_dependency")
        assert isinstance(dependency, dict), f"{relative}: approved_dependency missing"
        assert dependency.get("name") == spec.approved_dependency_name, (
            f"{relative}: approved dependency name mismatch"
        )
        assert dependency.get("specifier") == spec.approved_dependency_specifier, (
            f"{relative}: approved dependency specifier mismatch"
        )
        assert dependency.get("manifest") == spec.approved_dependency_manifest, (
            f"{relative}: approved dependency manifest mismatch"
        )
        assert dependency.get("change_count") == spec.approved_dependency_change_count, (
            f"{relative}: approved dependency change count mismatch"
        )
    else:
        assert payload.get("approved_dependency") in (None, {}), (
            f"{relative}: approved_dependency is not allowed"
        )
    assert payload.get("required_adr") == spec.required_adr, f"{relative}: required_adr mismatch"
    assert payload.get("expiry") == spec.expiry, f"{relative}: expiry mismatch"
    assert "revocation_path" in payload, f"{relative}: revocation_path missing"
    assert payload.get("reviewer_roles"), f"{relative}: reviewer_roles missing"
    assert payload.get("required_gates"), f"{relative}: required_gates missing"
    assert payload.get("evidence_references"), f"{relative}: evidence_references missing"
    return spec


def collect_approval_record(
    relative: str,
    payload: Any,
    approved_records: dict[tuple[str, str, str, str, str], set[str]],
    active_records: dict[tuple[str, str, str, str, str], set[str]],
    historical_records: dict[tuple[str, str, str, str, str], set[str]],
) -> None:
    if isinstance(payload, dict):
        true_keys = {key for key in APPROVAL_TRUE_KEYS if payload.get(key) is True}
        if true_keys:
            base_relative = relative.split(":", 1)[0].split("[", 1)[0]
            if base_relative in NON_PRODUCTION_AUTH_APPROVAL_RECORDS:
                return
            spec = validate_authorization_record(relative, payload)
            approved_records.setdefault(spec.tuple_key, set()).add(relative)
            if payload.get("authorization_active") is True:
                active_records.setdefault(spec.tuple_key, set()).add(relative)
            else:
                historical_records.setdefault(spec.tuple_key, set()).add(relative)
        elif true_keys != APPROVAL_TRUE_KEYS and true_keys:
            raise AssertionError(f"{relative}: partial authorization approval true keys")
        for key, value in payload.items():
            collect_approval_record(
                f"{relative}:{key}",
                value,
                approved_records,
                active_records,
                historical_records,
            )
    elif isinstance(payload, list):
        for index, item in enumerate(payload):
            collect_approval_record(
                f"{relative}[{index}]",
                item,
                approved_records,
                active_records,
                historical_records,
            )


def assert_global_false(relative: str, value: Any) -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            if key in GLOBAL_FALSE_KEYS:
                assert nested is False, f"{relative}: {key} must remain false"
            assert_global_false(relative, nested)
    elif isinstance(value, list):
        for item in value:
            assert_global_false(relative, item)


def assert_no_blocked_values(relative: str, value: Any) -> None:
    if isinstance(value, dict):
        for nested in value.values():
            assert_no_blocked_values(relative, nested)
    elif isinstance(value, list):
        for item in value:
            assert_no_blocked_values(relative, item)
    elif isinstance(value, str):
        lowered = value.lower()
        for marker in BLOCKED_VALUE_MARKERS:
            if marker == "private_key" and lowered in SAFE_POLICY_MARKER_VALUES:
                continue
            assert marker not in lowered, f"{relative}: blocked value marker {marker}"


def assert_no_forbidden_file_classes(root: Path) -> None:
    blocked_names = {"package.json", "package-lock.json", "pnpm-lock.yaml", "yarn.lock", "bun.lockb"}
    changed = run_git_diff(root)
    untracked = run_git(root, "ls-files", "--others", "--exclude-standard")
    for name in [*changed, *untracked]:
        path = Path(name)
        assert path.name not in blocked_names, f"package or lockfile changed: {name}"
        assert "migrations" not in path.parts, f"migration path changed: {name}"
        assert not name.startswith("services/brain-api/src/aion_brain/api/"), (
            f"runtime API route changed: {name}"
        )
        assert not name.startswith("packages/aion-sdk-python/src/"), (
            f"SDK or CLI source changed: {name}"
        )


def iter_json_payloads(root: Path) -> list[tuple[str, Any]]:
    bases = [
        root / "examples/release",
        root / "examples/platform",
        root / "examples/auth",
        root / "examples/connectors",
        root / "examples/modules",
        root / "operator-console-static/demo-data",
    ]
    payloads: list[tuple[str, Any]] = []
    for base in bases:
        if not base.exists():
            continue
        for path in sorted(base.glob("*.json")):
            payloads.append((str(path.relative_to(root)), load_json(path)))
    return payloads


def load_json(path: Path) -> dict[str, Any]:
    with path.open() as handle:
        payload = json.load(handle)
    assert isinstance(payload, dict), f"{path}: JSON root must be an object"
    return payload


def run_git_diff(root: Path) -> list[str]:
    base = comparison_base(root)
    args = ["diff", "--name-only", "--diff-filter=ACMRT"]
    if base:
        args.extend([base, "HEAD"])
    return run_git(root, *args)


def comparison_base(root: Path) -> str | None:
    candidates: list[str] = []
    github_base_ref = os.environ.get("GITHUB_BASE_REF")
    if github_base_ref:
        candidates.extend([f"origin/{github_base_ref}", github_base_ref])
    candidates.extend(["origin/main", "main"])

    for candidate in candidates:
        if git_ref_exists(root, candidate):
            merge_base = subprocess.run(
                ["git", "merge-base", "HEAD", candidate],
                cwd=root,
                capture_output=True,
                text=True,
                check=False,
            )
            if merge_base.returncode == 0 and merge_base.stdout.strip():
                return merge_base.stdout.strip()
    if git_ref_exists(root, "HEAD~1"):
        return "HEAD~1"
    return None


def git_ref_exists(root: Path, ref: str) -> bool:
    return (
        subprocess.run(
            ["git", "rev-parse", "--verify", "--quiet", ref],
            cwd=root,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        ).returncode
        == 0
    )


def run_git(root: Path, *args: str) -> list[str]:
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return []
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


if __name__ == "__main__":
    raise SystemExit(main())
