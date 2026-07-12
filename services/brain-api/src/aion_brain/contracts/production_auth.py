"""Disabled production auth core contracts owned by AION Brain."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from aion_brain.contracts.model_outputs import reject_hidden_or_secret_text

AUTHORIZATION_TRANSACTION_ID = "AION-151-PA-0001"
AUTHORIZATION_SCOPE = "disabled-production-auth-core"
IMPLEMENTATION_TASK = "AION-152"

ProductionAuthCoreState = Literal["implemented_disabled"]
ProductionAuthPolicyOutcome = Literal["blocked", "denied"]
ProductionAuthAuditEventType = Literal[
    "core_status_read",
    "policy_evaluation_preview",
    "guard_check",
    "configuration_validation",
    "no_go_finding",
]
PRODUCTION_AUTH_CORE_STATE: ProductionAuthCoreState = "implemented_disabled"

PROHIBITED_RUNTIME_FIELDS = (
    "runtime_enabled",
    "login_endpoint_enabled",
    "logout_endpoint_enabled",
    "callback_endpoint_enabled",
    "credential_storage_enabled",
    "password_storage_enabled",
    "token_issuance_enabled",
    "token_storage_enabled",
    "session_creation_enabled",
    "session_storage_enabled",
    "cookie_issuance_enabled",
    "cookie_session_persistence_enabled",
    "external_identity_provider_enabled",
    "oauth_runtime_enabled",
    "oidc_runtime_enabled",
    "saml_runtime_enabled",
    "external_calls_enabled",
    "network_client_enabled",
    "provider_sdk_enabled",
    "operator_write_execution_enabled",
    "connector_runtime_enabled",
    "module_activation_enabled",
    "sandbox_execution_enabled",
    "package_files_added",
    "lockfiles_added",
    "migrations_added",
    "runtime_api_routes_added",
    "v02_tag_created",
    "v02_release_created",
)

REQUIRED_REASON_CODES = (
    "production_auth_runtime_disabled",
    "runtime_enablement_guard_locked",
    "authorization_scope_implementation_only",
    "endpoint_surface_absent",
    "protected_material_storage_absent",
    "external_identity_provider_absent",
)

_PROTECTED_KEY_PARTS = {
    "access_token",
    "api_key",
    "apikey",
    "authorization_header",
    "bearer",
    "claim",
    "client_secret",
    "cookie",
    "credential",
    "id_token",
    "password",
    "private_key",
    "provider_payload",
    "raw_prompt",
    "refresh_token",
    "secret",
    "session_token",
    "token",
    "token_value",
}


class ProductionAuthCoreConfig(BaseModel):
    """Fail-closed internal production-auth core configuration."""

    model_config = ConfigDict(extra="forbid")

    authorization_transaction_id: str = AUTHORIZATION_TRANSACTION_ID
    authorization_scope: str = AUTHORIZATION_SCOPE
    authorization_consumed_by_task: str = IMPLEMENTATION_TASK
    authorization_reusable: bool = False
    authorization_expires_on_aion_152_merge: bool = True
    production_auth_core_implemented: bool = True
    production_auth_core_state: ProductionAuthCoreState = PRODUCTION_AUTH_CORE_STATE
    implementation_present: bool = True
    runtime_guard_hold_active: bool = True
    runtime_no_go_status: bool = True
    runtime_implementation_approved: bool = False
    runtime_enablement_guard_release_approved: bool = False
    runtime_enablement_guard_final_lock_release_approved: bool = False
    runtime_enablement_master_lock_release_approved: bool = False
    runtime_enabled: bool = False
    login_endpoint_enabled: bool = False
    logout_endpoint_enabled: bool = False
    callback_endpoint_enabled: bool = False
    credential_storage_enabled: bool = False
    password_storage_enabled: bool = False
    token_issuance_enabled: bool = False
    token_storage_enabled: bool = False
    session_creation_enabled: bool = False
    session_storage_enabled: bool = False
    cookie_issuance_enabled: bool = False
    cookie_session_persistence_enabled: bool = False
    external_identity_provider_enabled: bool = False
    oauth_runtime_enabled: bool = False
    oidc_runtime_enabled: bool = False
    saml_runtime_enabled: bool = False
    external_calls_enabled: bool = False
    network_client_enabled: bool = False
    provider_sdk_enabled: bool = False
    operator_write_execution_enabled: bool = False
    connector_runtime_enabled: bool = False
    module_activation_enabled: bool = False
    sandbox_execution_enabled: bool = False
    package_files_added: bool = False
    lockfiles_added: bool = False
    migrations_added: bool = False
    runtime_api_routes_added: bool = False
    v02_tag_created: bool = False
    v02_release_created: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def from_settings(cls, settings: object) -> ProductionAuthCoreConfig:
        """Map repository settings into a fail-closed internal config."""

        return cls(
            runtime_enabled=_setting(settings, "production_auth_enabled")
            or _setting(settings, "auth_runtime_enabled")
            or _setting(settings, "production_auth_core_runtime_enabled"),
            login_endpoint_enabled=_setting(settings, "auth_runtime_login_endpoint_enabled"),
            logout_endpoint_enabled=_setting(settings, "auth_runtime_logout_endpoint_enabled"),
            callback_endpoint_enabled=_setting(
                settings,
                "production_auth_callback_endpoint_enabled",
            ),
            credential_storage_enabled=_setting(settings, "auth_runtime_credentials_enabled")
            or _setting(settings, "auth_credentials_enabled"),
            password_storage_enabled=_setting(settings, "production_auth_password_storage_enabled"),
            token_issuance_enabled=_setting(settings, "auth_runtime_token_issuance_enabled"),
            token_storage_enabled=_setting(settings, "production_auth_token_storage_enabled"),
            session_creation_enabled=_setting(settings, "production_auth_session_creation_enabled"),
            session_storage_enabled=_setting(settings, "auth_runtime_session_persistence_enabled")
            or _setting(settings, "auth_sessions_enabled"),
            cookie_issuance_enabled=_setting(settings, "auth_runtime_cookie_issuance_enabled"),
            cookie_session_persistence_enabled=_setting(
                settings,
                "production_auth_cookie_session_persistence_enabled",
            ),
            external_identity_provider_enabled=_setting(
                settings,
                "auth_runtime_external_identity_enabled",
            )
            or _setting(settings, "external_identity_provider_enabled"),
            oauth_runtime_enabled=_setting(settings, "production_auth_oauth_runtime_enabled"),
            oidc_runtime_enabled=_setting(settings, "production_auth_oidc_runtime_enabled"),
            saml_runtime_enabled=_setting(settings, "production_auth_saml_runtime_enabled"),
            external_calls_enabled=_setting(settings, "production_auth_external_calls_enabled"),
            network_client_enabled=_setting(settings, "production_auth_network_client_enabled"),
            provider_sdk_enabled=_setting(settings, "production_auth_provider_sdk_enabled"),
            operator_write_execution_enabled=_setting(settings, "operator_action_execution_enabled")
            or _setting(settings, "action_authorization_write_allowed")
            or _setting(settings, "local_auth_write_actions_enabled"),
            connector_runtime_enabled=_setting(settings, "connector_runtime_enabled"),
            module_activation_enabled=_setting(settings, "module_activation_execution_enabled"),
            sandbox_execution_enabled=_setting(settings, "sandbox_execution_enabled"),
            metadata={"settings_source": "aion_brain.config.Settings"},
        )

    @field_validator("authorization_transaction_id")
    @classmethod
    def transaction_id_must_match(cls, value: str) -> str:
        if value != AUTHORIZATION_TRANSACTION_ID:
            raise ValueError("authorization_transaction_id must be AION-151-PA-0001")
        return value

    @field_validator("authorization_scope")
    @classmethod
    def scope_must_match(cls, value: str) -> str:
        if value != AUTHORIZATION_SCOPE:
            raise ValueError("authorization_scope must be disabled-production-auth-core")
        return value

    @field_validator("authorization_consumed_by_task")
    @classmethod
    def consumed_task_must_match(cls, value: str) -> str:
        if value != IMPLEMENTATION_TASK:
            raise ValueError("authorization_consumed_by_task must be AION-152")
        return value

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        _reject_protected_material(value)
        return value

    @model_validator(mode="after")
    def config_must_fail_closed(self) -> ProductionAuthCoreConfig:
        _require_authorized_disabled_state(self)
        return self


class ProductionAuthCoreStatus(BaseModel):
    """Internal status for the implemented-but-disabled production auth core."""

    model_config = ConfigDict(extra="forbid")

    status_id: str = Field(min_length=1)
    authorization_transaction_id: str = AUTHORIZATION_TRANSACTION_ID
    authorization_scope: str = AUTHORIZATION_SCOPE
    authorization_consumed_by_task: str = IMPLEMENTATION_TASK
    authorization_reusable: bool = False
    authorization_expires_on_aion_152_merge: bool = True
    production_auth_core_implemented: bool = True
    production_auth_core_state: ProductionAuthCoreState = PRODUCTION_AUTH_CORE_STATE
    implementation_state: ProductionAuthCoreState = PRODUCTION_AUTH_CORE_STATE
    implementation_present: bool = True
    runtime_guard_hold_active: bool = True
    runtime_no_go_status: bool = True
    runtime_implementation_approved: bool = False
    runtime_enablement_guard_release_approved: bool = False
    runtime_enablement_guard_final_lock_release_approved: bool = False
    runtime_enablement_master_lock_release_approved: bool = False
    runtime_enabled: bool = False
    login_endpoint_enabled: bool = False
    logout_endpoint_enabled: bool = False
    callback_endpoint_enabled: bool = False
    credential_storage_enabled: bool = False
    password_storage_enabled: bool = False
    token_issuance_enabled: bool = False
    token_storage_enabled: bool = False
    session_creation_enabled: bool = False
    session_storage_enabled: bool = False
    cookie_issuance_enabled: bool = False
    cookie_session_persistence_enabled: bool = False
    external_identity_provider_enabled: bool = False
    oauth_runtime_enabled: bool = False
    oidc_runtime_enabled: bool = False
    saml_runtime_enabled: bool = False
    external_calls_enabled: bool = False
    network_client_enabled: bool = False
    provider_sdk_enabled: bool = False
    operator_write_execution_enabled: bool = False
    connector_runtime_enabled: bool = False
    module_activation_enabled: bool = False
    sandbox_execution_enabled: bool = False
    package_files_added: bool = False
    lockfiles_added: bool = False
    migrations_added: bool = False
    runtime_api_routes_added: bool = False
    v02_tag_created: bool = False
    v02_release_created: bool = False
    blocker_reason_codes: list[str] = Field(default_factory=lambda: list(REQUIRED_REASON_CODES))
    blocker_count: int = Field(default=len(REQUIRED_REASON_CODES), ge=0)
    redacted: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime

    @field_validator("blocker_reason_codes")
    @classmethod
    def reason_codes_must_be_safe(cls, value: list[str]) -> list[str]:
        if not value:
            raise ValueError("blocker_reason_codes cannot be empty")
        for item in value:
            reject_hidden_or_secret_text(item, "production auth reason code")
        return value

    @field_validator("metadata")
    @classmethod
    def status_metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        _reject_protected_material(value)
        return value

    @model_validator(mode="after")
    def status_must_fail_closed(self) -> ProductionAuthCoreStatus:
        _require_authorized_disabled_state(self)
        if not self.redacted:
            raise ValueError("redacted must be true")
        return self


class ProductionAuthPolicyRequest(BaseModel):
    """Internal preview request for future production-auth operations."""

    model_config = ConfigDict(extra="forbid")

    request_id: str = Field(min_length=1)
    requested_operation: str = Field(min_length=1)
    owner_scope: list[str] = Field(default_factory=lambda: ["workspace:main"])
    authorization_transaction_id: str = AUTHORIZATION_TRANSACTION_ID
    authorization_scope: str = AUTHORIZATION_SCOPE
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None

    @field_validator("requested_operation")
    @classmethod
    def operation_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "production auth requested operation")
        return value.strip()

    @field_validator("owner_scope")
    @classmethod
    def owner_scope_must_not_be_empty(cls, value: list[str]) -> list[str]:
        cleaned = [item.strip() for item in value if item.strip()]
        if not cleaned:
            raise ValueError("owner_scope cannot be empty")
        return cleaned

    @field_validator("metadata")
    @classmethod
    def request_metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        _reject_protected_material(value)
        return value


class ProductionAuthPolicyDecision(BaseModel):
    """Fail-closed production-auth policy preview decision."""

    model_config = ConfigDict(extra="forbid")

    decision_id: str = Field(min_length=1)
    request_id: str = Field(min_length=1)
    outcome: ProductionAuthPolicyOutcome
    reason_codes: list[str] = Field(default_factory=lambda: list(REQUIRED_REASON_CODES))
    runtime_effect: bool = False
    policy_version: str = "production-auth-core-v0.2-disabled"
    authorization_transaction_id: str = AUTHORIZATION_TRANSACTION_ID
    created_at: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("reason_codes")
    @classmethod
    def decision_reason_codes_must_be_safe(cls, value: list[str]) -> list[str]:
        if not value:
            raise ValueError("reason_codes cannot be empty")
        for item in value:
            reject_hidden_or_secret_text(item, "production auth reason code")
        return value

    @field_validator("metadata")
    @classmethod
    def decision_metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        _reject_protected_material(value)
        return value

    @model_validator(mode="after")
    def decision_must_have_zero_runtime_effect(self) -> ProductionAuthPolicyDecision:
        if self.runtime_effect:
            raise ValueError("runtime_effect must be false")
        return self


class ProductionAuthAuditEvent(BaseModel):
    """Redacted audit event for the disabled production auth core."""

    model_config = ConfigDict(extra="forbid")

    event_id: str = Field(min_length=1)
    event_type: ProductionAuthAuditEventType
    request_id: str = Field(min_length=1)
    outcome: ProductionAuthPolicyOutcome
    reason_codes: list[str] = Field(default_factory=lambda: list(REQUIRED_REASON_CODES))
    runtime_effect: bool = False
    redacted: bool = True
    authorization_transaction_id: str = AUTHORIZATION_TRANSACTION_ID
    created_at: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("metadata")
    @classmethod
    def audit_metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        _reject_protected_material(value)
        return value

    @model_validator(mode="after")
    def audit_must_be_redacted_and_effect_free(self) -> ProductionAuthAuditEvent:
        if self.runtime_effect:
            raise ValueError("runtime_effect must be false")
        if not self.redacted:
            raise ValueError("redacted must be true")
        return self


class ProductionAuthProvenanceRecord(BaseModel):
    """Redacted provenance record for AION-152 implementation evidence."""

    model_config = ConfigDict(extra="forbid")

    provenance_id: str = Field(min_length=1)
    authorization_transaction_id: str = AUTHORIZATION_TRANSACTION_ID
    implementation_task: str = IMPLEMENTATION_TASK
    authorization_scope: str = AUTHORIZATION_SCOPE
    source_refs: list[str] = Field(min_length=1)
    runtime_effect: bool = False
    redacted: bool = True
    created_at: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("source_refs")
    @classmethod
    def source_refs_must_be_safe(cls, value: list[str]) -> list[str]:
        for item in value:
            reject_hidden_or_secret_text(item, "production auth source ref")
        return value

    @field_validator("metadata")
    @classmethod
    def provenance_metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        _reject_protected_material(value)
        return value

    @model_validator(mode="after")
    def provenance_must_be_redacted_and_effect_free(self) -> ProductionAuthProvenanceRecord:
        if self.runtime_effect:
            raise ValueError("runtime_effect must be false")
        if not self.redacted:
            raise ValueError("redacted must be true")
        if self.implementation_task != IMPLEMENTATION_TASK:
            raise ValueError("implementation_task must be AION-152")
        if self.authorization_scope != AUTHORIZATION_SCOPE:
            raise ValueError("authorization_scope must be disabled-production-auth-core")
        return self


class ProductionAuthDiagnosticSnapshot(BaseModel):
    """Redacted diagnostic snapshot for the disabled production auth core."""

    model_config = ConfigDict(extra="forbid")

    snapshot_id: str = Field(min_length=1)
    production_auth_core_implemented: bool = True
    production_auth_core_state: ProductionAuthCoreState = PRODUCTION_AUTH_CORE_STATE
    implementation_state: ProductionAuthCoreState = PRODUCTION_AUTH_CORE_STATE
    runtime_guard_hold_active: bool = True
    runtime_no_go_status: bool = True
    runtime_enabled: bool = False
    blocker_count: int = Field(ge=0)
    reason_codes: list[str] = Field(default_factory=lambda: list(REQUIRED_REASON_CODES))
    authorization_transaction_id: str = AUTHORIZATION_TRANSACTION_ID
    authorization_scope: str = AUTHORIZATION_SCOPE
    redacted: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime

    @field_validator("metadata")
    @classmethod
    def diagnostic_metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        _reject_protected_material(value)
        return value

    @model_validator(mode="after")
    def diagnostic_must_be_redacted_and_disabled(self) -> ProductionAuthDiagnosticSnapshot:
        if self.runtime_enabled:
            raise ValueError("runtime_enabled must be false")
        if not self.runtime_guard_hold_active:
            raise ValueError("runtime_guard_hold_active must be true")
        if not self.runtime_no_go_status:
            raise ValueError("runtime_no_go_status must be true")
        if not self.redacted:
            raise ValueError("redacted must be true")
        return self


def utc_now() -> datetime:
    """Return timezone-aware UTC time."""

    return datetime.now(UTC)


def _setting(settings: object, name: str) -> bool:
    return bool(getattr(settings, name, False))


def _require_authorized_disabled_state(model: object) -> None:
    if getattr(model, "authorization_transaction_id", AUTHORIZATION_TRANSACTION_ID) != (
        AUTHORIZATION_TRANSACTION_ID
    ):
        raise ValueError("authorization_transaction_id must be AION-151-PA-0001")
    if getattr(model, "authorization_scope", AUTHORIZATION_SCOPE) != AUTHORIZATION_SCOPE:
        raise ValueError("authorization_scope must be disabled-production-auth-core")
    if getattr(model, "authorization_consumed_by_task", IMPLEMENTATION_TASK) != IMPLEMENTATION_TASK:
        raise ValueError("authorization_consumed_by_task must be AION-152")
    if getattr(model, "authorization_reusable", False):
        raise ValueError("authorization_reusable must be false")
    if not getattr(model, "authorization_expires_on_aion_152_merge", True):
        raise ValueError("authorization_expires_on_aion_152_merge must be true")
    if not getattr(model, "production_auth_core_implemented", True):
        raise ValueError("production_auth_core_implemented must be true")
    if getattr(model, "production_auth_core_state", PRODUCTION_AUTH_CORE_STATE) != (
        PRODUCTION_AUTH_CORE_STATE
    ):
        raise ValueError("production_auth_core_state must be implemented_disabled")
    if not getattr(model, "implementation_present", True):
        raise ValueError("implementation_present must be true")
    if not getattr(model, "runtime_guard_hold_active", True):
        raise ValueError("runtime_guard_hold_active must be true")
    if not getattr(model, "runtime_no_go_status", True):
        raise ValueError("runtime_no_go_status must be true")
    for field_name in PROHIBITED_RUNTIME_FIELDS:
        if bool(getattr(model, field_name, False)):
            raise ValueError(f"{field_name} must be false")


def _reject_protected_material(value: object) -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            normalized = str(key).lower().replace("-", "_")
            if any(part in normalized for part in _PROTECTED_KEY_PARTS):
                raise ValueError("payload must not contain protected material keys")
            _reject_protected_material(nested)
        return
    if isinstance(value, list):
        for item in value:
            _reject_protected_material(item)
        return
    if isinstance(value, str):
        reject_hidden_or_secret_text(value, "production auth payload")


__all__ = [
    "AUTHORIZATION_SCOPE",
    "AUTHORIZATION_TRANSACTION_ID",
    "IMPLEMENTATION_TASK",
    "PRODUCTION_AUTH_CORE_STATE",
    "PROHIBITED_RUNTIME_FIELDS",
    "REQUIRED_REASON_CODES",
    "ProductionAuthAuditEvent",
    "ProductionAuthAuditEventType",
    "ProductionAuthCoreConfig",
    "ProductionAuthCoreState",
    "ProductionAuthCoreStatus",
    "ProductionAuthDiagnosticSnapshot",
    "ProductionAuthPolicyDecision",
    "ProductionAuthPolicyOutcome",
    "ProductionAuthPolicyRequest",
    "ProductionAuthProvenanceRecord",
    "utc_now",
]
