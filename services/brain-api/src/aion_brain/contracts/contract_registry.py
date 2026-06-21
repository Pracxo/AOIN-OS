"""Contract Registry public contracts owned by AION Brain."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from aion_brain.contracts.model_outputs import reject_secret_like_payload

ContractType = Literal[
    "pydantic_model",
    "api_request",
    "api_response",
    "sdk_resource",
    "cli_command",
    "policy_action",
    "env_setting",
    "feature_flag",
    "telemetry_event",
    "telemetry_node",
    "registry_resource",
    "capability_contract",
    "module_contract",
    "generic",
]
ContractStatus = Literal["active", "deprecated", "deleted", "unknown"]
InterfaceStatus = Literal["active", "deprecated", "deleted", "unknown"]
ContractVisibility = Literal["public", "internal", "operator", "sdk", "cli", "hidden"]
InterfaceType = Literal[
    "api_route",
    "openapi_schema",
    "sdk_method",
    "sdk_resource",
    "cli_command",
    "policy_action",
    "env_setting",
    "feature_flag",
    "telemetry_event",
    "telemetry_node",
    "registry_resource",
    "health_check",
    "generic",
]
SnapshotType = Literal[
    "manual",
    "release",
    "freeze",
    "baseline",
    "pre_change",
    "post_change",
    "sdk",
    "cli",
    "api",
]
SnapshotStatus = Literal["created", "failed"]


class ContractIndexRecord(BaseModel):
    """Index entry for a source-code-owned AION contract shape."""

    model_config = ConfigDict(extra="forbid")

    contract_index_id: str = Field(min_length=1)
    contract_key: str = Field(min_length=1)
    contract_type: ContractType
    source_path: str = Field(min_length=1)
    source_symbol: str = Field(min_length=1)
    status: ContractStatus
    visibility: ContractVisibility
    version: str = Field(min_length=1)
    schema_hash: str = Field(min_length=1)
    schema: dict[str, Any]  # type: ignore[assignment]
    owner_scope: list[str] = Field(min_length=1)
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    first_seen_at: datetime | None = None
    last_seen_at: datetime | None = None
    deprecated_at: datetime | None = None
    deleted_at: datetime | None = None

    @field_validator("schema", "metadata")
    @classmethod
    def payload_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value)
        return value


class InterfaceInventoryRecord(BaseModel):
    """Inventory entry for an exposed API, SDK, CLI, policy, setting, or telemetry interface."""

    model_config = ConfigDict(extra="forbid")

    interface_id: str = Field(min_length=1)
    interface_key: str = Field(min_length=1)
    interface_type: InterfaceType
    source_system: str = Field(min_length=1)
    status: InterfaceStatus
    visibility: ContractVisibility
    version: str = Field(min_length=1)
    path: str | None = None
    method: str | None = None
    command: str | None = None
    action: str | None = None
    setting_key: str | None = None
    feature_key: str | None = None
    telemetry_key: str | None = None
    resource_type: str | None = None
    schema_hash: str = Field(min_length=1)
    descriptor: dict[str, Any]
    owner_scope: list[str] = Field(min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)
    first_seen_at: datetime | None = None
    last_seen_at: datetime | None = None
    deprecated_at: datetime | None = None
    deleted_at: datetime | None = None

    @field_validator("descriptor", "metadata")
    @classmethod
    def payload_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value)
        return value


class ContractSnapshot(BaseModel):
    """Point-in-time manifest of indexed contract and interface shapes."""

    model_config = ConfigDict(extra="forbid")

    contract_snapshot_id: str = Field(min_length=1)
    trace_id: str | None = None
    snapshot_type: SnapshotType
    status: SnapshotStatus
    version: str = Field(min_length=1)
    owner_scope: list[str] = Field(min_length=1)
    contract_count: int = Field(ge=0)
    interface_count: int = Field(ge=0)
    policy_action_count: int = Field(ge=0)
    route_count: int = Field(ge=0)
    sdk_resource_count: int = Field(ge=0)
    cli_command_count: int = Field(ge=0)
    setting_count: int = Field(ge=0)
    telemetry_count: int = Field(ge=0)
    root_hash: str = Field(min_length=1)
    manifest: dict[str, Any]
    report: dict[str, Any]
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None

    @field_validator("manifest", "report", "metadata")
    @classmethod
    def payload_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value)
        return value


class ContractSnapshotCreateRequest(BaseModel):
    """API request for creating a contract snapshot."""

    model_config = ConfigDict(extra="forbid")

    scope: list[str] | None = None
    snapshot_type: SnapshotType = "manual"
    trace_id: str | None = None
    created_by: str | None = None


class ContractRegistryReportRequest(BaseModel):
    """API request for generating a registry report."""

    model_config = ConfigDict(extra="forbid")

    scope: list[str] | None = None
    trace_id: str | None = None
    created_by: str | None = None


class SeedCompatibilityRulesRequest(BaseModel):
    """API request for seeding default compatibility rules."""

    model_config = ConfigDict(extra="forbid")

    scope: list[str] | None = None
    dry_run: bool = True


class DismissFindingRequest(BaseModel):
    """API request for dismissing a drift finding."""

    model_config = ConfigDict(extra="forbid")

    actor_id: str | None = None
    reason: str = Field(min_length=1)

    @field_validator("reason")
    @classmethod
    def reason_must_be_safe(cls, value: str) -> str:
        reject_secret_like_payload(value)
        return value.strip()


class MigrationNote(BaseModel):
    """Informational compatibility migration note. It never executes steps."""

    model_config = ConfigDict(extra="forbid")

    migration_note_id: str = Field(min_length=1)
    trace_id: str | None = None
    compatibility_scan_id: str | None = None
    finding_id: str | None = None
    note_type: Literal[
        "breaking_change",
        "migration_required",
        "deprecation",
        "sdk_update",
        "cli_update",
        "policy_update",
        "docs_update",
        "generic",
    ]
    status: Literal["open", "archived", "resolved"]
    title: str = Field(min_length=1)
    description: str = Field(min_length=1)
    affected_contracts: list[str] = Field(default_factory=list)
    affected_interfaces: list[str] = Field(default_factory=list)
    migration_steps: list[str] = Field(min_length=1)
    owner_scope: list[str] = Field(min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None
    archived_at: datetime | None = None

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value)
        return value

    @field_validator("migration_steps")
    @classmethod
    def migration_steps_must_be_informational(cls, value: list[str]) -> list[str]:
        blocked = ("rm ", "delete from", "drop table", "curl ", "wget ", "python ", "bash ")
        for step in value:
            lowered = step.lower()
            if any(marker in lowered for marker in blocked):
                raise ValueError("migration_steps must not execute actions")
            reject_secret_like_payload(step)
        return value


class ContractRegistryReport(BaseModel):
    """Deterministic summary of contract registry health."""

    model_config = ConfigDict(extra="forbid")

    contract_report_id: str = Field(min_length=1)
    trace_id: str | None = None
    status: Literal["passed", "warning", "failed"]
    owner_scope: list[str] = Field(min_length=1)
    snapshot_id: str | None = None
    latest_scan_id: str | None = None
    contract_count: int = Field(ge=0)
    interface_count: int = Field(ge=0)
    active_breaking_findings: int = Field(ge=0)
    active_warning_findings: int = Field(ge=0)
    deprecated_count: int = Field(ge=0)
    missing_sdk_count: int = Field(ge=0)
    missing_cli_count: int = Field(ge=0)
    missing_policy_count: int = Field(ge=0)
    findings: list[dict[str, Any]] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None

    @field_validator("findings")
    @classmethod
    def findings_must_be_safe(cls, value: list[dict[str, Any]]) -> list[dict[str, Any]]:
        reject_secret_like_payload(value)
        return value

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value)
        return value

    @model_validator(mode="after")
    def status_must_reflect_breaking_findings(self) -> ContractRegistryReport:
        if self.active_breaking_findings > 0 and self.status == "passed":
            raise ValueError("report with active breaking findings cannot be passed")
        return self


__all__ = [
    "ContractIndexRecord",
    "ContractRegistryReport",
    "ContractRegistryReportRequest",
    "ContractSnapshot",
    "ContractSnapshotCreateRequest",
    "DismissFindingRequest",
    "InterfaceInventoryRecord",
    "MigrationNote",
    "SeedCompatibilityRulesRequest",
]
