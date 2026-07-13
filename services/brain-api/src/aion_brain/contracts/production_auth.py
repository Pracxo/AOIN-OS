"""Disabled production auth core contracts owned by AION Brain."""

from __future__ import annotations

import unicodedata
from datetime import UTC, datetime
from typing import Any, Literal, NoReturn

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from aion_brain.contracts.model_outputs import reject_hidden_or_secret_text
from aion_brain.production_auth.canonical import sha256_fingerprint
from aion_brain.production_auth.reason_codes import (
    REASON_CODE_REGISTRY_VERSION,
    REQUIRED_REASON_CODES,
    validate_reason_codes,
)

SCHEMA_VERSION = "production-auth-core/v1"
CANONICALIZATION_VERSION = "production-auth-canonical-json/v1"
POLICY_VERSION = "production-auth-policy/v1"

AUTHORIZATION_TRANSACTION_ID = "AION-151-PA-0001"
AUTHORIZATION_SCOPE = "disabled-production-auth-core"
IMPLEMENTATION_TASK = "AION-152"
STABILIZATION_AUTHORIZATION_TRANSACTION_ID = "AION-153-PA-0002"
STABILIZATION_AUTHORIZATION_TASK = "AION-154"
STABILIZATION_AUTHORIZATION_SCOPE = "disabled-production-auth-core-stabilization"

ProductionAuthCoreState = Literal["implemented_disabled"]
ProductionAuthPolicyOutcome = Literal["blocked", "denied"]
ProductionAuthPreviewOperation = Literal[
    "core_status_read",
    "policy_evaluation_preview",
    "guard_check",
    "configuration_validation",
    "no_go_inspection",
    "diagnostic_snapshot",
    "audit_evidence_build",
    "provenance_evidence_build",
]
ProductionAuthAuditEventType = ProductionAuthPreviewOperation
PRODUCTION_AUTH_CORE_STATE: ProductionAuthCoreState = "implemented_disabled"
PERMITTED_PREVIEW_OPERATIONS: tuple[str, ...] = (
    "core_status_read",
    "policy_evaluation_preview",
    "guard_check",
    "configuration_validation",
    "no_go_inspection",
    "diagnostic_snapshot",
    "audit_evidence_build",
    "provenance_evidence_build",
)

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
    "hidden_reasoning",
    "id_token",
    "password",
    "private_key",
    "provider_payload",
    "raw_identity_claim",
    "raw_prompt",
    "refresh_token",
    "secret",
    "session_token",
    "token",
    "token_value",
}
_PROTECTED_VALUE_MARKERS = (
    "access token",
    "refresh token",
    "id token",
    "session token",
    "authorization header",
    "private key",
    "client secret",
    "raw identity claim",
    "provider payload",
    "raw prompt",
    "hidden reasoning",
    "password",
    "credential",
    "cookie",
)


class ProductionAuthVersionedModel(BaseModel):
    """Common schema-version fields for production-auth contracts."""

    schema_version: str = SCHEMA_VERSION
    canonicalization_version: str = CANONICALIZATION_VERSION
    policy_version: str = POLICY_VERSION
    reason_code_registry_version: str = REASON_CODE_REGISTRY_VERSION

    @field_validator("schema_version")
    @classmethod
    def schema_version_must_match(cls, value: str) -> str:
        if value != SCHEMA_VERSION:
            raise ValueError(f"schema_version must be {SCHEMA_VERSION}")
        return value

    @field_validator("canonicalization_version")
    @classmethod
    def canonicalization_version_must_match(cls, value: str) -> str:
        if value != CANONICALIZATION_VERSION:
            raise ValueError(f"canonicalization_version must be {CANONICALIZATION_VERSION}")
        return value

    @field_validator("policy_version")
    @classmethod
    def policy_version_must_match(cls, value: str) -> str:
        if value != POLICY_VERSION:
            raise ValueError(f"policy_version must be {POLICY_VERSION}")
        return value

    @field_validator("reason_code_registry_version")
    @classmethod
    def reason_code_registry_version_must_match(cls, value: str) -> str:
        if value != REASON_CODE_REGISTRY_VERSION:
            raise ValueError(
                f"reason_code_registry_version must be {REASON_CODE_REGISTRY_VERSION}"
            )
        return value


class ProductionAuthFingerprintedModel(ProductionAuthVersionedModel):
    """Versioned evidence model with a deterministic SHA-256 fingerprint."""

    fingerprint: str | None = None

    @model_validator(mode="after")
    def fingerprint_must_match_payload(self) -> ProductionAuthFingerprintedModel:
        expected = _fingerprint_for_model(self)
        if self.fingerprint is None:
            object.__setattr__(self, "fingerprint", expected)
        elif self.fingerprint != expected:
            raise ValueError("fingerprint must match canonical evidence payload")
        return self


class _FrozenDict(dict[str, Any]):
    """Small immutable dict for nested evidence metadata."""

    def _blocked(self, *_args: object, **_kwargs: object) -> NoReturn:
        raise TypeError("production-auth evidence metadata is immutable")

    def __setitem__(self, key: str, value: Any) -> NoReturn:
        self._blocked(key, value)

    def __delitem__(self, key: str) -> NoReturn:
        self._blocked(key)

    def clear(self) -> NoReturn:
        self._blocked()

    def pop(self, key: str, default: Any = None) -> NoReturn:  # noqa: ARG002
        self._blocked(key, default)

    def popitem(self) -> NoReturn:
        self._blocked()

    def setdefault(self, key: str, default: Any = None) -> NoReturn:
        self._blocked(key, default)

    def update(self, *args: Any, **kwargs: Any) -> NoReturn:
        self._blocked(*args, **kwargs)


class ProductionAuthCoreConfig(ProductionAuthVersionedModel):
    """Fail-closed internal production-auth core configuration."""

    model_config = ConfigDict(extra="forbid")

    authorization_transaction_id: str = AUTHORIZATION_TRANSACTION_ID
    authorization_scope: str = AUTHORIZATION_SCOPE
    authorization_consumed_by_task: str = IMPLEMENTATION_TASK
    authorization_reusable: bool = False
    authorization_expires_on_aion_152_merge: bool = True
    implementation_authorization_transaction_id: str = AUTHORIZATION_TRANSACTION_ID
    implementation_authorization_task: str = IMPLEMENTATION_TASK
    implementation_authorization_scope: str = AUTHORIZATION_SCOPE
    stabilization_authorization_transaction_id: str = STABILIZATION_AUTHORIZATION_TRANSACTION_ID
    stabilization_authorization_task: str = STABILIZATION_AUTHORIZATION_TASK
    stabilization_authorization_scope: str = STABILIZATION_AUTHORIZATION_SCOPE
    stabilization_authorization_reusable: bool = False
    stabilization_authorization_expires_on_aion_154_merge: bool = True
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

    @field_validator("authorization_transaction_id", "implementation_authorization_transaction_id")
    @classmethod
    def transaction_id_must_match(cls, value: str) -> str:
        if value != AUTHORIZATION_TRANSACTION_ID:
            raise ValueError("authorization_transaction_id must be AION-151-PA-0001")
        return value

    @field_validator("authorization_scope", "implementation_authorization_scope")
    @classmethod
    def scope_must_match(cls, value: str) -> str:
        if value != AUTHORIZATION_SCOPE:
            raise ValueError("authorization_scope must be disabled-production-auth-core")
        return value

    @field_validator("authorization_consumed_by_task", "implementation_authorization_task")
    @classmethod
    def consumed_task_must_match(cls, value: str) -> str:
        if value != IMPLEMENTATION_TASK:
            raise ValueError("authorization_consumed_by_task must be AION-152")
        return value

    @field_validator("stabilization_authorization_transaction_id")
    @classmethod
    def stabilization_transaction_id_must_match(cls, value: str) -> str:
        if value != STABILIZATION_AUTHORIZATION_TRANSACTION_ID:
            raise ValueError(
                "stabilization_authorization_transaction_id must be AION-153-PA-0002"
            )
        return value

    @field_validator("stabilization_authorization_task")
    @classmethod
    def stabilization_task_must_match(cls, value: str) -> str:
        if value != STABILIZATION_AUTHORIZATION_TASK:
            raise ValueError("stabilization_authorization_task must be AION-154")
        return value

    @field_validator("stabilization_authorization_scope")
    @classmethod
    def stabilization_scope_must_match(cls, value: str) -> str:
        if value != STABILIZATION_AUTHORIZATION_SCOPE:
            raise ValueError(
                "stabilization_authorization_scope must be "
                "disabled-production-auth-core-stabilization"
            )
        return value

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        _reject_protected_material(value)
        return dict(value)

    @model_validator(mode="after")
    def config_must_fail_closed(self) -> ProductionAuthCoreConfig:
        _require_authorized_disabled_state(self)
        return self


class ProductionAuthCoreStatus(ProductionAuthFingerprintedModel):
    """Internal status for the implemented-but-disabled production auth core."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    status_id: str = Field(min_length=1)
    authorization_transaction_id: str = AUTHORIZATION_TRANSACTION_ID
    authorization_scope: str = AUTHORIZATION_SCOPE
    authorization_consumed_by_task: str = IMPLEMENTATION_TASK
    authorization_reusable: bool = False
    authorization_expires_on_aion_152_merge: bool = True
    implementation_authorization_transaction_id: str = AUTHORIZATION_TRANSACTION_ID
    implementation_authorization_task: str = IMPLEMENTATION_TASK
    implementation_authorization_scope: str = AUTHORIZATION_SCOPE
    stabilization_authorization_transaction_id: str = STABILIZATION_AUTHORIZATION_TRANSACTION_ID
    stabilization_authorization_task: str = STABILIZATION_AUTHORIZATION_TASK
    stabilization_authorization_scope: str = STABILIZATION_AUTHORIZATION_SCOPE
    stabilization_authorization_reusable: bool = False
    stabilization_authorization_expires_on_aion_154_merge: bool = True
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
    blocker_reason_codes: tuple[str, ...] = Field(
        default_factory=lambda: tuple(REQUIRED_REASON_CODES)
    )
    blocker_count: int = Field(default=len(REQUIRED_REASON_CODES), ge=0)
    redacted: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime

    @field_validator("blocker_reason_codes")
    @classmethod
    def reason_codes_must_be_registered(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return validate_reason_codes(value)

    @field_validator("metadata")
    @classmethod
    def status_metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        _reject_protected_material(value)
        return _freeze_mapping(value)

    @model_validator(mode="after")
    def status_must_fail_closed(self) -> ProductionAuthCoreStatus:
        _require_authorized_disabled_state(self)
        if not self.redacted:
            raise ValueError("redacted must be true")
        if self.blocker_count != len(self.blocker_reason_codes):
            raise ValueError("blocker_count must match blocker_reason_codes")
        return self


class ProductionAuthPolicyRequest(ProductionAuthVersionedModel):
    """Internal preview request for future production-auth operations."""

    model_config = ConfigDict(extra="forbid")

    request_id: str = Field(min_length=1)
    requested_operation: ProductionAuthPreviewOperation
    owner_scope: list[str] = Field(default_factory=lambda: ["workspace:main"])
    authorization_transaction_id: str = AUTHORIZATION_TRANSACTION_ID
    authorization_scope: str = AUTHORIZATION_SCOPE
    stabilization_authorization_transaction_id: str = STABILIZATION_AUTHORIZATION_TRANSACTION_ID
    stabilization_authorization_scope: str = STABILIZATION_AUTHORIZATION_SCOPE
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None

    @field_validator("requested_operation")
    @classmethod
    def operation_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "production auth requested operation")
        if value not in PERMITTED_PREVIEW_OPERATIONS:
            raise ValueError("unknown production-auth preview operation")
        return value

    @field_validator("owner_scope")
    @classmethod
    def owner_scope_must_not_be_empty(cls, value: list[str]) -> list[str]:
        cleaned = [item.strip() for item in value if item.strip()]
        if not cleaned:
            raise ValueError("owner_scope cannot be empty")
        return cleaned

    @field_validator("authorization_transaction_id")
    @classmethod
    def request_transaction_id_must_match(cls, value: str) -> str:
        if value != AUTHORIZATION_TRANSACTION_ID:
            raise ValueError("authorization_transaction_id must be AION-151-PA-0001")
        return value

    @field_validator("authorization_scope")
    @classmethod
    def request_scope_must_match(cls, value: str) -> str:
        if value != AUTHORIZATION_SCOPE:
            raise ValueError("authorization_scope must be disabled-production-auth-core")
        return value

    @field_validator("metadata")
    @classmethod
    def request_metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        _reject_protected_material(value)
        return dict(value)


class ProductionAuthPolicyDecision(ProductionAuthFingerprintedModel):
    """Fail-closed production-auth policy preview decision."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    decision_id: str = Field(min_length=1)
    request_id: str = Field(min_length=1)
    requested_operation: ProductionAuthPreviewOperation = "policy_evaluation_preview"
    outcome: ProductionAuthPolicyOutcome
    reason_codes: tuple[str, ...] = Field(default_factory=lambda: tuple(REQUIRED_REASON_CODES))
    runtime_effect: bool = False
    authorization_transaction_id: str = AUTHORIZATION_TRANSACTION_ID
    authorization_scope: str = AUTHORIZATION_SCOPE
    stabilization_authorization_transaction_id: str = STABILIZATION_AUTHORIZATION_TRANSACTION_ID
    stabilization_authorization_task: str = STABILIZATION_AUTHORIZATION_TASK
    stabilization_authorization_scope: str = STABILIZATION_AUTHORIZATION_SCOPE
    stabilization_authorization_reusable: bool = False
    stabilization_authorization_expires_on_aion_154_merge: bool = True
    created_at: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("reason_codes")
    @classmethod
    def decision_reason_codes_must_be_registered(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return validate_reason_codes(value)

    @field_validator("metadata")
    @classmethod
    def decision_metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        _reject_protected_material(value)
        return _freeze_mapping(value)

    @model_validator(mode="after")
    def decision_must_have_zero_runtime_effect(self) -> ProductionAuthPolicyDecision:
        if self.runtime_effect:
            raise ValueError("runtime_effect must be false")
        return self


class ProductionAuthAuditEvent(ProductionAuthFingerprintedModel):
    """Redacted audit event for the disabled production auth core."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    event_id: str = Field(min_length=1)
    event_type: ProductionAuthAuditEventType
    request_id: str = Field(min_length=1)
    outcome: ProductionAuthPolicyOutcome
    reason_codes: tuple[str, ...] = Field(default_factory=lambda: tuple(REQUIRED_REASON_CODES))
    runtime_effect: bool = False
    redacted: bool = True
    authorization_transaction_id: str = AUTHORIZATION_TRANSACTION_ID
    authorization_scope: str = AUTHORIZATION_SCOPE
    stabilization_authorization_transaction_id: str = STABILIZATION_AUTHORIZATION_TRANSACTION_ID
    stabilization_authorization_task: str = STABILIZATION_AUTHORIZATION_TASK
    stabilization_authorization_scope: str = STABILIZATION_AUTHORIZATION_SCOPE
    created_at: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("reason_codes")
    @classmethod
    def audit_reason_codes_must_be_registered(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return validate_reason_codes(value)

    @field_validator("metadata")
    @classmethod
    def audit_metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        _reject_protected_material(value)
        return _freeze_mapping(value)

    @model_validator(mode="after")
    def audit_must_be_redacted_and_effect_free(self) -> ProductionAuthAuditEvent:
        if self.runtime_effect:
            raise ValueError("runtime_effect must be false")
        if not self.redacted:
            raise ValueError("redacted must be true")
        return self


class ProductionAuthProvenanceRecord(ProductionAuthFingerprintedModel):
    """Redacted provenance record for AION-152 implementation evidence."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    provenance_id: str = Field(min_length=1)
    authorization_transaction_id: str = AUTHORIZATION_TRANSACTION_ID
    implementation_task: str = IMPLEMENTATION_TASK
    authorization_scope: str = AUTHORIZATION_SCOPE
    stabilization_authorization_transaction_id: str = STABILIZATION_AUTHORIZATION_TRANSACTION_ID
    stabilization_authorization_task: str = STABILIZATION_AUTHORIZATION_TASK
    stabilization_authorization_scope: str = STABILIZATION_AUTHORIZATION_SCOPE
    stabilization_authorization_reusable: bool = False
    stabilization_authorization_expires_on_aion_154_merge: bool = True
    source_refs: tuple[str, ...] = Field(min_length=1)
    runtime_effect: bool = False
    redacted: bool = True
    created_at: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("source_refs")
    @classmethod
    def source_refs_must_be_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        for item in value:
            reject_hidden_or_secret_text(item, "production auth source ref")
            _reject_protected_material(item)
        return tuple(value)

    @field_validator("metadata")
    @classmethod
    def provenance_metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        _reject_protected_material(value)
        return _freeze_mapping(value)

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


class ProductionAuthDiagnosticSnapshot(ProductionAuthFingerprintedModel):
    """Redacted diagnostic snapshot for the disabled production auth core."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    snapshot_id: str = Field(min_length=1)
    production_auth_core_implemented: bool = True
    production_auth_core_state: ProductionAuthCoreState = PRODUCTION_AUTH_CORE_STATE
    implementation_state: ProductionAuthCoreState = PRODUCTION_AUTH_CORE_STATE
    runtime_guard_hold_active: bool = True
    runtime_no_go_status: bool = True
    runtime_enabled: bool = False
    blocker_count: int = Field(ge=0)
    reason_codes: tuple[str, ...] = Field(default_factory=lambda: tuple(REQUIRED_REASON_CODES))
    authorization_transaction_id: str = AUTHORIZATION_TRANSACTION_ID
    authorization_scope: str = AUTHORIZATION_SCOPE
    stabilization_authorization_transaction_id: str = STABILIZATION_AUTHORIZATION_TRANSACTION_ID
    stabilization_authorization_task: str = STABILIZATION_AUTHORIZATION_TASK
    stabilization_authorization_scope: str = STABILIZATION_AUTHORIZATION_SCOPE
    redacted: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime

    @field_validator("reason_codes")
    @classmethod
    def diagnostic_reason_codes_must_be_registered(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return validate_reason_codes(value)

    @field_validator("metadata")
    @classmethod
    def diagnostic_metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        _reject_protected_material(value)
        return _freeze_mapping(value)

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
        if self.blocker_count != len(self.reason_codes):
            raise ValueError("blocker_count must match reason_codes")
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
    if getattr(
        model,
        "stabilization_authorization_transaction_id",
        STABILIZATION_AUTHORIZATION_TRANSACTION_ID,
    ) != STABILIZATION_AUTHORIZATION_TRANSACTION_ID:
        raise ValueError("stabilization_authorization_transaction_id must be AION-153-PA-0002")
    if getattr(
        model,
        "stabilization_authorization_scope",
        STABILIZATION_AUTHORIZATION_SCOPE,
    ) != STABILIZATION_AUTHORIZATION_SCOPE:
        raise ValueError(
            "stabilization_authorization_scope must be disabled-production-auth-core-stabilization"
        )
    if getattr(model, "stabilization_authorization_reusable", False):
        raise ValueError("stabilization_authorization_reusable must be false")
    if not getattr(model, "stabilization_authorization_expires_on_aion_154_merge", True):
        raise ValueError("stabilization_authorization_expires_on_aion_154_merge must be true")
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
            normalized = _normalize_protected_text(str(key))
            if any(part in normalized for part in _PROTECTED_KEY_PARTS):
                raise ValueError("payload must not contain protected material keys")
            _reject_protected_material(nested)
        return
    if isinstance(value, list | tuple):
        for item in value:
            _reject_protected_material(item)
        return
    if isinstance(value, str):
        reject_hidden_or_secret_text(value, "production auth payload")
        lowered = _normalize_protected_value(value)
        if any(marker in lowered for marker in _PROTECTED_VALUE_MARKERS):
            raise ValueError("payload must not contain protected material values")


def _freeze_mapping(value: dict[str, Any]) -> _FrozenDict:
    return _FrozenDict(value)


def _normalize_protected_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).casefold()
    return normalized.replace("-", "_").replace(" ", "_")


def _normalize_protected_value(value: str) -> str:
    return unicodedata.normalize("NFKC", value).casefold().replace("-", " ")


def _fingerprint_for_model(model: BaseModel) -> str:
    payload = model.model_dump(mode="json", exclude={"fingerprint"})
    return sha256_fingerprint(payload)


__all__ = [
    "AUTHORIZATION_SCOPE",
    "AUTHORIZATION_TRANSACTION_ID",
    "CANONICALIZATION_VERSION",
    "IMPLEMENTATION_TASK",
    "PERMITTED_PREVIEW_OPERATIONS",
    "POLICY_VERSION",
    "PRODUCTION_AUTH_CORE_STATE",
    "PROHIBITED_RUNTIME_FIELDS",
    "REASON_CODE_REGISTRY_VERSION",
    "REQUIRED_REASON_CODES",
    "SCHEMA_VERSION",
    "STABILIZATION_AUTHORIZATION_SCOPE",
    "STABILIZATION_AUTHORIZATION_TASK",
    "STABILIZATION_AUTHORIZATION_TRANSACTION_ID",
    "ProductionAuthAuditEvent",
    "ProductionAuthAuditEventType",
    "ProductionAuthCoreConfig",
    "ProductionAuthCoreState",
    "ProductionAuthCoreStatus",
    "ProductionAuthDiagnosticSnapshot",
    "ProductionAuthPolicyDecision",
    "ProductionAuthPolicyOutcome",
    "ProductionAuthPolicyRequest",
    "ProductionAuthPreviewOperation",
    "ProductionAuthProvenanceRecord",
    "utc_now",
]
