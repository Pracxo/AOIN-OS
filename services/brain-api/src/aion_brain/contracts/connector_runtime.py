"""Disabled external connector runtime contracts owned by AION Brain."""

from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from aion_brain.contracts.model_outputs import (
    reject_hidden_or_secret_text,
    reject_secret_like_payload,
)

ConnectorRuntimeStatusValue = Literal["disabled", "preview", "blocked", "passed", "failed"]
ConnectorRuntimeBlockerType = Literal[
    "connector_runtime_disabled",
    "external_calls_disabled",
    "credentials_disabled",
    "token_storage_disabled",
    "activation_disabled",
    "route_registration_disabled",
    "network_clients_absent",
    "provider_sdks_absent",
    "unsafe_payload",
    "manifest_external_calls_required",
    "manifest_credentials_required",
    "manifest_routes_declared",
    "generic",
]
ConnectorRuntimeBlockerSeverity = Literal["low", "medium", "high", "critical"]
ConnectorRuntimeBlockerStatus = Literal["open", "resolved"]

_DOTTED_LOWERCASE_RE = re.compile(r"^[a-z][a-z0-9]*(?:\.[a-z0-9]+)*$")


class ConnectorRuntimeBlocker(BaseModel):
    """One disabled connector-runtime blocker."""

    model_config = ConfigDict(extra="forbid")

    connector_runtime_blocker_id: str = Field(min_length=1)
    blocker_type: ConnectorRuntimeBlockerType
    severity: ConnectorRuntimeBlockerSeverity
    status: ConnectorRuntimeBlockerStatus
    reason: str = Field(min_length=1)
    recommended_action: str = Field(min_length=1)
    source_type: str | None = None
    source_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime

    @field_validator("reason", "recommended_action")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "connector runtime blocker text")
        return value

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        _reject_payload_except_controlled(value)
        return value


class ConnectorRuntimeStatus(BaseModel):
    """Hard-off connector runtime status with mock preview flags."""

    model_config = ConfigDict(extra="forbid")

    status_id: str = Field(min_length=1)
    connector_runtime_enabled: bool
    connector_mock_preview_enabled: bool
    connector_egress_preview_enabled: bool
    connector_ingress_preview_enabled: bool
    connector_external_calls_enabled: bool
    connector_credentials_enabled: bool
    connector_token_storage_enabled: bool
    connector_activation_enabled: bool
    connector_route_registration_enabled: bool
    blockers: list[ConnectorRuntimeBlocker] = Field(default_factory=list)
    warnings: list[dict[str, Any]] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime

    @field_validator("warnings", "metadata")
    @classmethod
    def payload_must_be_safe(cls, value: Any) -> Any:
        _reject_payload_except_controlled(value)
        return value

    @model_validator(mode="after")
    def runtime_must_stay_disabled(self) -> ConnectorRuntimeStatus:
        if self.connector_runtime_enabled:
            raise ValueError("connector_runtime_enabled must be false")
        if self.connector_external_calls_enabled:
            raise ValueError("connector_external_calls_enabled must be false")
        if self.connector_credentials_enabled:
            raise ValueError("connector_credentials_enabled must be false")
        if self.connector_token_storage_enabled:
            raise ValueError("connector_token_storage_enabled must be false")
        if self.connector_activation_enabled:
            raise ValueError("connector_activation_enabled must be false")
        if self.connector_route_registration_enabled:
            raise ValueError("connector_route_registration_enabled must be false")
        return self


class MockConnectorManifest(BaseModel):
    """Synthetic mock connector manifest accepted only for local previews."""

    model_config = ConfigDict(extra="forbid")

    connector_key: str
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    version: str = Field(min_length=1)
    owner_scope: list[str] = Field(min_length=1)
    connector_type: str = Field(min_length=1)
    supported_modes: list[str] = Field(default_factory=lambda: ["dry_run"])
    declared_capabilities: list[str] = Field(default_factory=list)
    required_policy_actions: list[str] = Field(default_factory=list)
    required_scopes: list[str] = Field(default_factory=list)
    sandbox_required: bool
    dry_run_supported: bool
    external_calls_required: bool
    credentials_required: bool
    routes_declared: list[dict[str, Any]] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("connector_key")
    @classmethod
    def connector_key_must_be_dotted_lowercase(cls, value: str) -> str:
        cleaned = value.strip()
        if not _DOTTED_LOWERCASE_RE.match(cleaned):
            raise ValueError("connector_key must be dotted lowercase text")
        return cleaned

    @field_validator("name", "description", "version", "connector_type")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("value cannot be empty")
        reject_hidden_or_secret_text(cleaned, "mock connector manifest text")
        return cleaned

    @field_validator(
        "owner_scope",
        "supported_modes",
        "declared_capabilities",
        "required_policy_actions",
        "required_scopes",
    )
    @classmethod
    def lists_must_be_safe(cls, value: list[str]) -> list[str]:
        cleaned = [item.strip() for item in value if item.strip()]
        for item in cleaned:
            reject_hidden_or_secret_text(item, "mock connector manifest list")
        return cleaned

    @field_validator("routes_declared", "metadata")
    @classmethod
    def payload_must_be_safe(cls, value: Any) -> Any:
        _reject_payload_except_controlled(value)
        return value

    @model_validator(mode="after")
    def manifest_must_be_preview_only(self) -> MockConnectorManifest:
        if not self.owner_scope:
            raise ValueError("owner_scope cannot be empty")
        if self.external_calls_required:
            raise ValueError("external_calls_required must be false in AION-108")
        if self.credentials_required:
            raise ValueError("credentials_required must be false in AION-108")
        if self.routes_declared:
            raise ValueError("routes_declared must be empty in AION-108")
        if not self.dry_run_supported:
            raise ValueError("dry_run_supported must be true")
        return self


class MockConnectorManifestValidationResult(BaseModel):
    """Mock connector manifest validation result."""

    model_config = ConfigDict(extra="forbid")

    connector_manifest_validation_id: str = Field(min_length=1)
    connector_key: str
    status: ConnectorRuntimeStatusValue
    valid: bool
    external_calls_required: bool
    credentials_required: bool
    routes_declared_count: int
    blockers: list[ConnectorRuntimeBlocker] = Field(default_factory=list)
    warnings: list[dict[str, Any]] = Field(default_factory=list)
    normalized_manifest: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime

    @field_validator("warnings", "normalized_manifest", "metadata")
    @classmethod
    def payload_must_be_safe(cls, value: Any) -> Any:
        _reject_payload_except_controlled(value)
        return value

    @model_validator(mode="after")
    def validation_must_not_authorize_runtime(self) -> MockConnectorManifestValidationResult:
        if self.external_calls_required:
            raise ValueError("external_calls_required must be false")
        if self.credentials_required:
            raise ValueError("credentials_required must be false")
        if self.routes_declared_count != 0:
            raise ValueError("routes_declared_count must be zero")
        if self.valid and self.blockers:
            raise ValueError("valid validation cannot include blockers")
        return self


class ConnectorEgressPreviewRequest(BaseModel):
    """Request a mock-only connector egress preview."""

    model_config = ConfigDict(extra="forbid")

    trace_id: str | None = None
    connector_key: str
    owner_scope: list[str] = Field(min_length=1)
    preview_type: str = "dry_run"
    payload_summary: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None

    @field_validator("connector_key")
    @classmethod
    def connector_key_must_be_dotted_lowercase(cls, value: str) -> str:
        return MockConnectorManifest.connector_key_must_be_dotted_lowercase(value)

    @field_validator("owner_scope")
    @classmethod
    def owner_scope_must_not_be_empty(cls, value: list[str]) -> list[str]:
        cleaned = [item.strip() for item in value if item.strip()]
        if not cleaned:
            raise ValueError("owner_scope cannot be empty")
        return cleaned

    @field_validator("preview_type")
    @classmethod
    def preview_type_must_be_dry_run(cls, value: str) -> str:
        if value != "dry_run":
            raise ValueError("preview_type must be dry_run")
        return value

    @field_validator("payload_summary", "metadata")
    @classmethod
    def payloads_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        _reject_payload_except_controlled(value)
        return value


class ConnectorEgressPreviewResult(BaseModel):
    """Mock connector egress preview result. It never permits egress."""

    model_config = ConfigDict(extra="forbid")

    connector_egress_preview_id: str = Field(min_length=1)
    trace_id: str | None = None
    connector_key: str
    status: ConnectorRuntimeStatusValue
    egress_allowed: bool
    external_call_allowed: bool
    credentials_present: bool
    blocked_fields: list[str] = Field(default_factory=list)
    blockers: list[ConnectorRuntimeBlocker] = Field(default_factory=list)
    warnings: list[dict[str, Any]] = Field(default_factory=list)
    redacted_payload_summary: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime

    @field_validator("warnings", "redacted_payload_summary", "metadata")
    @classmethod
    def payload_must_be_safe(cls, value: Any) -> Any:
        _reject_payload_except_controlled(value)
        return value

    @model_validator(mode="after")
    def egress_must_remain_blocked(self) -> ConnectorEgressPreviewResult:
        if self.egress_allowed:
            raise ValueError("egress_allowed must be false")
        if self.external_call_allowed:
            raise ValueError("external_call_allowed must be false")
        if self.credentials_present:
            raise ValueError("credentials_present must be false")
        return self


class ConnectorIngressPreviewRequest(BaseModel):
    """Request a mock-only connector ingress preview."""

    model_config = ConfigDict(extra="forbid")

    trace_id: str | None = None
    connector_key: str
    owner_scope: list[str] = Field(min_length=1)
    preview_type: str = "dry_run"
    response_summary: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None

    @field_validator("connector_key")
    @classmethod
    def connector_key_must_be_dotted_lowercase(cls, value: str) -> str:
        return MockConnectorManifest.connector_key_must_be_dotted_lowercase(value)

    @field_validator("owner_scope")
    @classmethod
    def owner_scope_must_not_be_empty(cls, value: list[str]) -> list[str]:
        return ConnectorEgressPreviewRequest.owner_scope_must_not_be_empty(value)

    @field_validator("preview_type")
    @classmethod
    def preview_type_must_be_dry_run(cls, value: str) -> str:
        return ConnectorEgressPreviewRequest.preview_type_must_be_dry_run(value)

    @field_validator("response_summary", "metadata")
    @classmethod
    def payloads_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        _reject_payload_except_controlled(value)
        return value


class ConnectorIngressPreviewResult(BaseModel):
    """Mock connector ingress preview result. Returned data is untrusted."""

    model_config = ConfigDict(extra="forbid")

    connector_ingress_preview_id: str = Field(min_length=1)
    trace_id: str | None = None
    connector_key: str
    status: ConnectorRuntimeStatusValue
    trusted: bool
    provenance_required: bool
    redaction_applied: bool
    prompt_injection_scan_required: bool
    normalized_response_summary: dict[str, Any] = Field(default_factory=dict)
    blockers: list[ConnectorRuntimeBlocker] = Field(default_factory=list)
    warnings: list[dict[str, Any]] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime

    @field_validator("normalized_response_summary", "warnings", "metadata")
    @classmethod
    def payload_must_be_safe(cls, value: Any) -> Any:
        _reject_payload_except_controlled(value)
        return value

    @model_validator(mode="after")
    def ingress_must_remain_untrusted(self) -> ConnectorIngressPreviewResult:
        if self.trusted:
            raise ValueError("trusted must be false")
        if not self.provenance_required:
            raise ValueError("provenance_required must be true")
        if not self.redaction_applied:
            raise ValueError("redaction_applied must be true")
        if not self.prompt_injection_scan_required:
            raise ValueError("prompt_injection_scan_required must be true")
        return self


class ConnectorRuntimeAuditRequest(BaseModel):
    """Request a local disabled-connector runtime audit."""

    model_config = ConfigDict(extra="forbid")

    trace_id: str | None = None
    owner_scope: list[str] = Field(default_factory=lambda: ["workspace:main"])
    include_examples: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None

    @field_validator("owner_scope")
    @classmethod
    def owner_scope_must_not_be_empty(cls, value: list[str]) -> list[str]:
        cleaned = [item.strip() for item in value if item.strip()]
        if not cleaned:
            raise ValueError("owner_scope cannot be empty")
        return cleaned

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        _reject_payload_except_controlled(value)
        return value


class ConnectorRuntimeAuditResult(BaseModel):
    """Audit proof that connector runtime remains disabled."""

    model_config = ConfigDict(extra="forbid")

    connector_runtime_audit_id: str = Field(min_length=1)
    trace_id: str | None = None
    status: ConnectorRuntimeStatusValue
    owner_scope: list[str] = Field(min_length=1)
    checks_run: list[str] = Field(default_factory=list)
    findings: list[dict[str, Any]] = Field(default_factory=list)
    runtime_disabled: bool
    external_calls_disabled: bool
    credentials_disabled: bool
    token_storage_disabled: bool
    activation_disabled: bool
    route_registration_disabled: bool
    network_clients_absent: bool
    provider_sdks_absent: bool
    recommendations: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime

    @field_validator("findings", "metadata")
    @classmethod
    def payload_must_be_safe(cls, value: Any) -> Any:
        _reject_payload_except_controlled(value)
        return value

    @model_validator(mode="after")
    def audit_must_confirm_disabled_boundaries(self) -> ConnectorRuntimeAuditResult:
        if self.status == "passed":
            for key in (
                "runtime_disabled",
                "external_calls_disabled",
                "credentials_disabled",
                "token_storage_disabled",
                "activation_disabled",
                "route_registration_disabled",
                "network_clients_absent",
                "provider_sdks_absent",
            ):
                if getattr(self, key) is not True:
                    raise ValueError(f"{key} must be true for passed status")
        return self


def utc_now() -> datetime:
    """Return timezone-aware UTC time."""

    return datetime.now(UTC)


def _reject_payload_except_controlled(value: object) -> None:
    """Reject unsafe material while allowing controlled disabled-boundary fields."""

    if isinstance(value, dict):
        for key, nested in value.items():
            lowered = str(key).lower().replace("-", "_")
            allowed_exact = {
                "activation_disabled",
                "activation_enabled",
                "audit_required",
                "blocker_type",
                "code",
                "connector_activation_enabled",
                "connector_credentials_enabled",
                "connector_egress_preview_enabled",
                "connector_external_calls_enabled",
                "connector_ingress_preview_enabled",
                "connector_mock_preview_enabled",
                "connector_route_registration_enabled",
                "connector_runtime_enabled",
                "connector_token_storage_enabled",
                "credentials_disabled",
                "credentials_present",
                "credentials_required",
                "dry_run_supported",
                "egress_allowed",
                "external_call_allowed",
                "external_calls_disabled",
                "external_calls_required",
                "finding",
                "network_clients_absent",
                "preview_type",
                "provider_sdks_absent",
                "route_registration_disabled",
                "routes_declared",
                "runtime_disabled",
                "status",
                "token_storage_disabled",
                "trusted",
            }
            if lowered in allowed_exact:
                _reject_payload_except_controlled(nested)
                continue
            reject_secret_like_payload({key: nested})
        return
    if isinstance(value, list):
        for item in value:
            _reject_payload_except_controlled(item)
        return
    if isinstance(value, str):
        reject_hidden_or_secret_text(value, "connector runtime payload")


__all__ = [
    "ConnectorEgressPreviewRequest",
    "ConnectorEgressPreviewResult",
    "ConnectorIngressPreviewRequest",
    "ConnectorIngressPreviewResult",
    "ConnectorRuntimeAuditRequest",
    "ConnectorRuntimeAuditResult",
    "ConnectorRuntimeBlocker",
    "ConnectorRuntimeStatus",
    "MockConnectorManifest",
    "MockConnectorManifestValidationResult",
    "utc_now",
]
