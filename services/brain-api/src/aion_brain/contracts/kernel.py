"""Kernel assembly, diagnostics, and export contracts."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from aion_brain.contracts.diagnostics import DiagnosticCheck

KernelBootStatus = Literal["starting", "ready", "degraded", "failed"]
KernelServiceType = Literal[
    "api",
    "repository",
    "adapter",
    "service",
    "runtime",
    "policy",
    "memory",
    "reasoning",
    "execution",
    "visual",
    "observability",
    "regression",
    "infrastructure",
]
KernelServiceStatus = Literal["registered", "healthy", "degraded", "unhealthy", "disabled"]
KernelSelfTestStatus = Literal["passed", "failed", "degraded"]
ArchitectureBoundaryStatus = Literal["passed", "failed"]
_SECRET_KEYS = {"password", "secret", "token", "api_key", "private_key", "authorization"}


class KernelAdapterConfig(BaseModel):
    """Provider-neutral adapter selection for the assembled Brain."""

    model_config = ConfigDict(extra="forbid")

    runtime_adapter: str = Field(min_length=1)
    semantic_memory_adapter: str = Field(min_length=1)
    graph_memory_adapter: str = Field(min_length=1)
    model_gateway_adapter: str = Field(min_length=1)
    policy_adapter: str = Field(min_length=1)
    object_store_adapter: str = Field(min_length=1)
    observability_adapter: str = Field(min_length=1)
    module_runtime_adapters: list[str] = Field(min_length=1)
    evaluation_adapters: list[str] = Field(min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator(
        "runtime_adapter",
        "semantic_memory_adapter",
        "graph_memory_adapter",
        "model_gateway_adapter",
        "policy_adapter",
        "object_store_adapter",
        "observability_adapter",
    )
    @classmethod
    def adapter_name_must_not_be_empty(cls, value: str) -> str:
        """Reject blank adapter names."""
        if not value.strip():
            raise ValueError("adapter names cannot be empty")
        return value

    @field_validator("module_runtime_adapters", "evaluation_adapters")
    @classmethod
    def adapter_lists_must_not_contain_empty_names(cls, value: list[str]) -> list[str]:
        """Reject empty adapter names."""
        if any(not item.strip() for item in value):
            raise ValueError("adapter names cannot be empty")
        return value

    @field_validator("metadata")
    @classmethod
    def metadata_must_not_contain_secrets(cls, value: dict[str, Any]) -> dict[str, Any]:
        """Reject secret-like adapter metadata."""
        _reject_secret_keys(value)
        return value


class KernelBootRecord(BaseModel):
    """Persisted kernel boot outcome."""

    model_config = ConfigDict(extra="forbid")

    boot_id: str
    service_name: str
    version: str
    env: str
    status: KernelBootStatus
    adapter_config: KernelAdapterConfig
    diagnostics: dict[str, Any]
    started_at: datetime | None
    completed_at: datetime | None


class KernelServiceRecord(BaseModel):
    """Registered service or adapter in the Brain kernel."""

    model_config = ConfigDict(extra="forbid")

    service_record_id: str
    service_name: str
    service_type: KernelServiceType
    adapter_name: str
    status: KernelServiceStatus
    health: dict[str, Any]
    metadata: dict[str, Any]
    created_at: datetime | None
    updated_at: datetime | None


class KernelSelfTestRequest(BaseModel):
    """Request for a local, deterministic Brain kernel self-test."""

    model_config = ConfigDict(extra="forbid")

    scope: list[str] = Field(min_length=1)
    include_database: bool = True
    include_policy: bool = True
    include_memory: bool = True
    include_reasoning: bool = True
    include_execution: bool = True
    include_visual: bool = True
    include_replay: bool = True
    dry_run: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)


class KernelSelfTestResult(BaseModel):
    """Persisted local self-test outcome."""

    model_config = ConfigDict(extra="forbid")

    self_test_id: str
    status: KernelSelfTestStatus
    checks: list[DiagnosticCheck]
    report: dict[str, Any]
    created_at: datetime
    completed_at: datetime | None


class KernelStatus(BaseModel):
    """Current assembled Brain kernel status."""

    model_config = ConfigDict(extra="forbid")

    service_name: str
    version: str
    env: str
    status: str
    uptime_seconds: int | None
    adapter_config: KernelAdapterConfig
    services: list[KernelServiceRecord]
    latest_boot: KernelBootRecord | None
    latest_self_test: KernelSelfTestResult | None
    generated_at: datetime


class ContractExport(BaseModel):
    """OpenAPI and core Pydantic schema export."""

    model_config = ConfigDict(extra="forbid")

    export_id: str
    version: str
    contracts: dict[str, Any]
    openapi: dict[str, Any]
    generated_at: datetime


class ArchitectureBoundaryReport(BaseModel):
    """Architecture boundary scan result."""

    model_config = ConfigDict(extra="forbid")

    report_id: str
    status: ArchitectureBoundaryStatus
    violations: list[dict[str, Any]]
    checked_paths: list[str]
    created_at: datetime


def _reject_secret_keys(value: object) -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            normalized = str(key).lower().replace("-", "_")
            if any(secret in normalized for secret in _SECRET_KEYS):
                raise ValueError("metadata must not contain secret-like keys")
            _reject_secret_keys(nested)
    elif isinstance(value, list):
        for item in value:
            _reject_secret_keys(item)
