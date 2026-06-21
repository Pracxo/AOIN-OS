"""Interface compatibility and drift contracts owned by AION Brain."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from aion_brain.contracts.contract_registry import ContractRegistryReport, MigrationNote
from aion_brain.contracts.model_outputs import reject_secret_like_payload
from aion_brain.contracts.versioning import reject_secret_like_keys

CompatibilityStatus = Literal["compatible", "warning", "incompatible"]
MigrationBaselineStatus = Literal["passed", "warning", "failed"]
ReleaseArtifactStatus = Literal["draft", "complete", "failed"]
CompatibilityRuleType = Literal[
    "no_removed_required_field",
    "no_removed_route",
    "no_removed_sdk_method",
    "no_removed_cli_command",
    "no_removed_policy_action",
    "no_removed_env_setting",
    "no_removed_telemetry_event",
    "no_removed_registry_resource",
    "no_type_narrowing",
    "no_visibility_leak",
    "no_secret_schema",
    "no_domain_interface",
    "generic",
]
CompatibilityRuleStatus = Literal["active", "disabled"]
CompatibilitySeverity = Literal["low", "medium", "high", "critical"]
DriftFindingType = Literal[
    "removed_contract",
    "removed_field",
    "removed_route",
    "removed_sdk_method",
    "removed_cli_command",
    "removed_policy_action",
    "removed_setting",
    "removed_telemetry_event",
    "type_changed",
    "visibility_changed",
    "required_field_added",
    "schema_hash_changed",
    "missing_sdk_binding",
    "missing_cli_binding",
    "missing_policy_action",
    "secret_leak",
    "domain_drift",
    "generic",
]
DriftFindingStatus = Literal["open", "resolved", "dismissed", "archived"]
CompatibilityMode = Literal["dry_run", "controlled"]
CompatibilityScanStatus = Literal["passed", "warning", "failed", "dry_run", "blocked_by_policy"]


class CompatibilityMatrix(BaseModel):
    """Compatibility record for one AION release version."""

    model_config = ConfigDict(extra="forbid")

    compatibility_matrix_id: str = Field(min_length=1)
    version: str = Field(min_length=1)
    api_version: str = Field(min_length=1)
    sdk_version: str = Field(min_length=1)
    python_version: str = Field(min_length=1)
    docker_compose_version: str | None = None
    postgres_version: str | None = None
    redis_version: str | None = None
    nats_version: str | None = None
    opa_version: str | None = None
    optional_adapters: dict[str, Any] = Field(default_factory=dict)
    compatibility: dict[str, Any] = Field(default_factory=dict)
    status: CompatibilityStatus
    created_at: datetime | None = None


class MigrationBaseline(BaseModel):
    """Deterministic migration baseline summary."""

    model_config = ConfigDict(extra="forbid")

    migration_baseline_id: str = Field(min_length=1)
    schema_version: str = Field(min_length=1)
    migration_count: int = Field(ge=0)
    migration_hash: str = Field(min_length=1)
    destructive_migrations: list[str] = Field(default_factory=list)
    tables: list[str] = Field(default_factory=list)
    status: MigrationBaselineStatus
    report: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None


class ReleaseArtifactManifest(BaseModel):
    """Metadata-only release artifact manifest."""

    model_config = ConfigDict(extra="forbid")

    release_artifact_id: str = Field(min_length=1)
    version: str = Field(min_length=1)
    status: ReleaseArtifactStatus
    artifacts: dict[str, Any] = Field(default_factory=dict)
    checksums: dict[str, str] = Field(default_factory=dict)
    report: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None


class SDKCompatibilityReport(BaseModel):
    """SDK/API compatibility check result."""

    model_config = ConfigDict(extra="forbid")

    report_id: str = Field(min_length=1)
    api_version: str = Field(min_length=1)
    sdk_version: str = Field(min_length=1)
    compatible: bool
    checked_endpoints: list[str] = Field(default_factory=list)
    missing_endpoints: list[str] = Field(default_factory=list)
    mismatched_contracts: list[dict[str, Any]] = Field(default_factory=list)
    warnings: list[dict[str, Any]] = Field(default_factory=list)
    generated_at: datetime

    def model_post_init(self, __context: object) -> None:
        """Reject secret-like warning or mismatch payloads."""
        for payload in [*self.mismatched_contracts, *self.warnings]:
            reject_secret_like_keys(payload)


class CompatibilityRule(BaseModel):
    """Rule used by the deterministic compatibility scanner."""

    model_config = ConfigDict(extra="forbid")

    compatibility_rule_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    status: CompatibilityRuleStatus
    rule_type: CompatibilityRuleType
    severity: CompatibilitySeverity
    applies_to: list[str] = Field(min_length=1)
    rule: dict[str, Any]
    owner_scope: list[str] = Field(min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    disabled_at: datetime | None = None

    @field_validator("rule", "metadata")
    @classmethod
    def payload_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value)
        return value


class InterfaceDriftFinding(BaseModel):
    """Compatibility issue detected by comparing interface snapshots."""

    model_config = ConfigDict(extra="forbid")

    drift_finding_id: str = Field(min_length=1)
    trace_id: str | None = None
    compatibility_scan_id: str | None = None
    finding_type: DriftFindingType
    interface_type: str = Field(min_length=1)
    contract_key: str | None = None
    interface_key: str | None = None
    source_system: str = Field(min_length=1)
    severity: CompatibilitySeverity
    status: DriftFindingStatus
    breaking: bool
    title: str = Field(min_length=1)
    description: str = Field(min_length=1)
    old_ref: str | None = None
    new_ref: str | None = None
    recommended_action: str = Field(min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None
    resolved_at: datetime | None = None
    dismissed_at: datetime | None = None

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value)
        return value


class CompatibilityScanRequest(BaseModel):
    """Request to compare current or stored interface snapshots."""

    model_config = ConfigDict(extra="forbid")

    compatibility_scan_id: str | None = None
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    mode: CompatibilityMode = "dry_run"
    owner_scope: list[str] = Field(min_length=1)
    baseline_snapshot_id: str | None = None
    candidate_snapshot_id: str | None = None
    scan_scope: list[str] = Field(default_factory=list)
    rule_ids: list[str] = Field(default_factory=list)
    create_notifications: bool = False
    create_operator_items: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value)
        return value


class CompatibilityScan(BaseModel):
    """Result of one deterministic compatibility scan."""

    model_config = ConfigDict(extra="forbid")

    compatibility_scan_id: str = Field(min_length=1)
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    status: CompatibilityScanStatus
    mode: CompatibilityMode
    owner_scope: list[str] = Field(min_length=1)
    baseline_snapshot_id: str | None = None
    candidate_snapshot_id: str | None = None
    scan_scope: list[str] = Field(default_factory=list)
    rules_applied: list[str] = Field(default_factory=list)
    findings_count: int = Field(ge=0)
    breaking_count: int = Field(ge=0)
    warning_count: int = Field(ge=0)
    passed_count: int = Field(ge=0)
    findings: list[InterfaceDriftFinding] = Field(default_factory=list)
    result: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None
    completed_at: datetime | None = None

    @field_validator("result", "metadata")
    @classmethod
    def payload_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value)
        return value


__all__ = [
    "CompatibilityMatrix",
    "CompatibilityRule",
    "CompatibilityScan",
    "CompatibilityScanRequest",
    "ContractRegistryReport",
    "InterfaceDriftFinding",
    "MigrationBaseline",
    "MigrationNote",
    "ReleaseArtifactManifest",
    "SDKCompatibilityReport",
]
