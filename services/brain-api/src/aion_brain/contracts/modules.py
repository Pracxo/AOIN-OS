"""Module runtime contracts owned by AION Brain."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

RuntimeType = Literal["local_internal", "local_stub", "http", "mcp"]
ModuleRuntimeStatus = Literal["registered", "active", "disabled"]
ModuleHealthStatus = Literal["unknown", "healthy", "degraded", "unhealthy"]
InvocationMode = Literal["dry_run", "controlled"]
CapabilityRuntimeBindingStatus = Literal["active", "disabled"]
ModuleHealthCheckStatus = Literal["healthy", "degraded", "unhealthy"]
CapabilityInvocationResultStatus = Literal[
    "completed",
    "dry_run",
    "not_implemented",
    "blocked_by_policy",
    "capability_not_found",
    "runtime_not_found",
    "runtime_unhealthy",
    "failed",
]

_SECRET_KEYS = {"api_key", "secret", "token", "password", "private_key"}
_SECRET_MARKERS = ("api_key=", "secret=", "token=", "password=", "private_key=", "sk-")


class ModuleRuntime(BaseModel):
    """Registered runtime boundary for a future module."""

    model_config = ConfigDict(extra="forbid")

    runtime_id: str = Field(min_length=1)
    module_id: str = Field(min_length=1)
    version: str = Field(min_length=1)
    runtime_type: RuntimeType
    endpoint_ref: str | None = None
    status: ModuleRuntimeStatus = "registered"
    health_status: ModuleHealthStatus = "unknown"
    config: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None
    updated_at: datetime | None = None
    last_health_check_at: datetime | None = None

    @field_validator("endpoint_ref")
    @classmethod
    def endpoint_ref_has_no_secret_markers(cls, value: str | None) -> str | None:
        """Reject endpoint references that look like they contain credentials."""
        if value is None:
            return value
        lowered = value.lower()
        if any(marker in lowered for marker in _SECRET_MARKERS):
            raise ValueError("endpoint_ref must not contain secrets")
        return value

    @field_validator("config")
    @classmethod
    def config_has_no_secret_keys(cls, value: dict[str, Any]) -> dict[str, Any]:
        """Reject secret-like config keys recursively."""
        secret_key = _find_secret_key(value)
        if secret_key is not None:
            raise ValueError(f"config must not contain secret key: {secret_key}")
        return value


class CapabilityRuntimeBinding(BaseModel):
    """Binding between a capability contract and a module runtime."""

    model_config = ConfigDict(extra="forbid")

    binding_id: str = Field(min_length=1)
    capability_id: str = Field(min_length=1)
    module_id: str = Field(min_length=1)
    runtime_id: str = Field(min_length=1)
    invocation_mode: InvocationMode
    status: CapabilityRuntimeBindingStatus = "active"
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ModuleHealthCheck(BaseModel):
    """Persisted runtime health check result."""

    model_config = ConfigDict(extra="forbid")

    health_check_id: str = Field(min_length=1)
    runtime_id: str = Field(min_length=1)
    module_id: str = Field(min_length=1)
    status: ModuleHealthCheckStatus
    latency_ms: int | None = Field(default=None, ge=0)
    details: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class ModuleRuntimeRegistrationRequest(BaseModel):
    """Request to register a module runtime and optional bindings."""

    model_config = ConfigDict(extra="forbid")

    runtime: ModuleRuntime
    bind_capabilities: list[str] = Field(default_factory=list)
    activate: bool = False


class ModuleRuntimeRegistrationResponse(BaseModel):
    """Runtime registration response."""

    model_config = ConfigDict(extra="forbid")

    registered: bool
    runtime_id: str
    module_id: str
    version: str
    binding_count: int
    status: str
    reason: str | None = None


class CapabilityBindingRequest(BaseModel):
    """Request to bind a capability to a runtime."""

    model_config = ConfigDict(extra="forbid")

    capability_id: str = Field(min_length=1)
    module_id: str = Field(min_length=1)
    runtime_id: str = Field(min_length=1)
    invocation_mode: InvocationMode
    status: CapabilityRuntimeBindingStatus = "active"


class CapabilityInvocationRequest(BaseModel):
    """Request to invoke a capability through the runtime gateway."""

    model_config = ConfigDict(extra="forbid")

    invocation_id: str = Field(min_length=1)
    trace_id: str | None = None
    execution_id: str | None = None
    step_run_id: str | None = None
    capability_id: str = Field(min_length=1)
    actor_id: str | None = None
    workspace_id: str | None = None
    mode: InvocationMode = "dry_run"
    payload: dict[str, Any] = Field(default_factory=dict)
    approval_present: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


class CapabilityInvocationResult(BaseModel):
    """Provider-neutral capability invocation result."""

    model_config = ConfigDict(extra="forbid")

    invocation_id: str
    capability_id: str
    runtime_id: str | None
    status: CapabilityInvocationResultStatus
    output: dict[str, Any]
    error: dict[str, Any]
    policy_decision_id: str | None
    latency_ms: int | None = Field(default=None, ge=0)
    created_at: datetime


def _find_secret_key(value: Any) -> str | None:
    if isinstance(value, dict):
        for key, item in value.items():
            normalized = str(key).lower()
            if normalized in _SECRET_KEYS:
                return str(key)
            nested = _find_secret_key(item)
            if nested is not None:
                return nested
    if isinstance(value, list):
        for item in value:
            nested = _find_secret_key(item)
            if nested is not None:
                return nested
    return None
