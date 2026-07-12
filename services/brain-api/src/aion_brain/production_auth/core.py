"""Internal disabled production-auth core service."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from uuid import uuid4

from aion_brain.contracts.production_auth import (
    REQUIRED_REASON_CODES,
    ProductionAuthAuditEvent,
    ProductionAuthAuditEventType,
    ProductionAuthCoreConfig,
    ProductionAuthCoreStatus,
    ProductionAuthDiagnosticSnapshot,
    ProductionAuthPolicyDecision,
    ProductionAuthPolicyRequest,
    ProductionAuthProvenanceRecord,
    utc_now,
)
from aion_brain.production_auth.audit import ProductionAuthAuditBuilder
from aion_brain.production_auth.diagnostics import ProductionAuthDiagnosticBuilder
from aion_brain.production_auth.policy import ProductionAuthPolicyEvaluator
from aion_brain.production_auth.provenance import ProductionAuthProvenanceBuilder


class ProductionAuthCoreService:
    """Expose implementation evidence while keeping production auth disabled."""

    def __init__(
        self,
        config: ProductionAuthCoreConfig,
        *,
        policy_evaluator: ProductionAuthPolicyEvaluator | None = None,
        audit_builder: ProductionAuthAuditBuilder | None = None,
        provenance_builder: ProductionAuthProvenanceBuilder | None = None,
        diagnostic_builder: ProductionAuthDiagnosticBuilder | None = None,
        clock: Callable[[], datetime] = utc_now,
        id_factory: Callable[[str], str] | None = None,
    ) -> None:
        self._config = config
        self._policy_evaluator = policy_evaluator or ProductionAuthPolicyEvaluator(clock=clock)
        self._audit_builder = audit_builder or ProductionAuthAuditBuilder(clock=clock)
        self._provenance_builder = provenance_builder or ProductionAuthProvenanceBuilder(
            clock=clock
        )
        self._diagnostic_builder = diagnostic_builder or ProductionAuthDiagnosticBuilder(
            clock=clock
        )
        self._clock = clock
        self._id_factory = id_factory or (lambda prefix: f"{prefix}-{uuid4().hex}")

    @property
    def config(self) -> ProductionAuthCoreConfig:
        """Return the fail-closed core configuration."""

        return self._config

    def status(self) -> ProductionAuthCoreStatus:
        """Return implemented-disabled status with all runtime flags false."""

        return ProductionAuthCoreStatus(
            status_id=self._id_factory("prod-auth-core-status"),
            authorization_transaction_id=self._config.authorization_transaction_id,
            authorization_scope=self._config.authorization_scope,
            authorization_consumed_by_task=self._config.authorization_consumed_by_task,
            authorization_reusable=self._config.authorization_reusable,
            authorization_expires_on_aion_152_merge=(
                self._config.authorization_expires_on_aion_152_merge
            ),
            production_auth_core_implemented=self._config.production_auth_core_implemented,
            production_auth_core_state=self._config.production_auth_core_state,
            implementation_state=self._config.production_auth_core_state,
            implementation_present=self._config.implementation_present,
            runtime_guard_hold_active=self._config.runtime_guard_hold_active,
            runtime_no_go_status=self._config.runtime_no_go_status,
            runtime_implementation_approved=self._config.runtime_implementation_approved,
            runtime_enablement_guard_release_approved=(
                self._config.runtime_enablement_guard_release_approved
            ),
            runtime_enablement_guard_final_lock_release_approved=(
                self._config.runtime_enablement_guard_final_lock_release_approved
            ),
            runtime_enablement_master_lock_release_approved=(
                self._config.runtime_enablement_master_lock_release_approved
            ),
            runtime_enabled=self._config.runtime_enabled,
            login_endpoint_enabled=self._config.login_endpoint_enabled,
            logout_endpoint_enabled=self._config.logout_endpoint_enabled,
            callback_endpoint_enabled=self._config.callback_endpoint_enabled,
            credential_storage_enabled=self._config.credential_storage_enabled,
            password_storage_enabled=self._config.password_storage_enabled,
            token_issuance_enabled=self._config.token_issuance_enabled,
            token_storage_enabled=self._config.token_storage_enabled,
            session_creation_enabled=self._config.session_creation_enabled,
            session_storage_enabled=self._config.session_storage_enabled,
            cookie_issuance_enabled=self._config.cookie_issuance_enabled,
            cookie_session_persistence_enabled=self._config.cookie_session_persistence_enabled,
            external_identity_provider_enabled=self._config.external_identity_provider_enabled,
            oauth_runtime_enabled=self._config.oauth_runtime_enabled,
            oidc_runtime_enabled=self._config.oidc_runtime_enabled,
            saml_runtime_enabled=self._config.saml_runtime_enabled,
            external_calls_enabled=self._config.external_calls_enabled,
            network_client_enabled=self._config.network_client_enabled,
            provider_sdk_enabled=self._config.provider_sdk_enabled,
            operator_write_execution_enabled=self._config.operator_write_execution_enabled,
            connector_runtime_enabled=self._config.connector_runtime_enabled,
            module_activation_enabled=self._config.module_activation_enabled,
            sandbox_execution_enabled=self._config.sandbox_execution_enabled,
            package_files_added=self._config.package_files_added,
            lockfiles_added=self._config.lockfiles_added,
            migrations_added=self._config.migrations_added,
            runtime_api_routes_added=self._config.runtime_api_routes_added,
            v02_tag_created=self._config.v02_tag_created,
            v02_release_created=self._config.v02_release_created,
            blocker_reason_codes=list(REQUIRED_REASON_CODES),
            blocker_count=len(REQUIRED_REASON_CODES),
            redacted=True,
            metadata={"scope": "internal", "public_route_added": False},
            created_at=self._clock(),
        )

    def evaluate_policy(
        self,
        request: ProductionAuthPolicyRequest,
    ) -> ProductionAuthPolicyDecision:
        """Return a fail-closed policy decision with zero runtime effect."""

        return self._policy_evaluator.evaluate(request, self._config)

    def build_audit_event(
        self,
        *,
        event_type: ProductionAuthAuditEventType,
        decision: ProductionAuthPolicyDecision,
        metadata: dict[str, object] | None = None,
    ) -> ProductionAuthAuditEvent:
        """Build a redacted audit event for a blocked internal preview."""

        return self._audit_builder.build(
            event_type=event_type,
            decision=decision,
            metadata=metadata,
        )

    def build_provenance_record(
        self,
        *,
        source_refs: list[str],
        metadata: dict[str, object] | None = None,
    ) -> ProductionAuthProvenanceRecord:
        """Build a redacted provenance record for AION-152 implementation evidence."""

        return self._provenance_builder.build(source_refs=source_refs, metadata=metadata)

    def diagnostic_snapshot(self) -> ProductionAuthDiagnosticSnapshot:
        """Return safe kernel diagnostics for the disabled core."""

        return self._diagnostic_builder.build(self._config)


__all__ = ["ProductionAuthCoreService"]
