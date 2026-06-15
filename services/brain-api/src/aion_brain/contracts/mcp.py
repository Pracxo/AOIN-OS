"""MCP adapter contracts owned by AION Brain."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

MCPTransportType = Literal["stdio", "http", "sse", "in_memory_fake"]
MCPServerStatus = Literal["registered", "active", "disabled"]
MCPHealthStatus = Literal["unknown", "healthy", "degraded", "unhealthy"]
MCPMappingStatus = Literal["active", "disabled"]
MCPRiskLevel = Literal["low", "medium", "high", "critical"]
MCPSyncStatus = Literal[
    "completed",
    "failed",
    "blocked_by_policy",
    "server_unavailable",
    "mcp_disabled",
]
MCPInvocationMode = Literal["dry_run", "controlled"]
MCPInvocationStatus = Literal[
    "dry_run",
    "completed",
    "blocked_by_policy",
    "server_unavailable",
    "tool_not_found",
    "mcp_disabled",
    "failed",
    "not_implemented",
]
MCPServerHealthStatus = Literal["healthy", "degraded", "unhealthy", "unavailable"]

_SECRET_KEYS = {"api_key", "apikey", "secret", "token", "password", "private_key"}
_SECRET_MARKERS = ("api_key=", "apikey=", "secret=", "token=", "password=", "sk-")
_SHELL_CONTROL_MARKERS = (";", "&&", "||", "|", "`", "$(", ">", "<")


class MCPServerRecord(BaseModel):
    """A registered external MCP server boundary."""

    model_config = ConfigDict(extra="forbid")

    mcp_server_id: str = Field(min_length=1)
    server_name: str = Field(min_length=1)
    transport_type: MCPTransportType
    endpoint_ref: str | None
    status: MCPServerStatus
    health_status: MCPHealthStatus
    config: dict[str, Any] = Field(default_factory=dict)
    owner_scope: list[str] = Field(min_length=1)
    created_at: datetime | None
    updated_at: datetime | None
    last_health_check_at: datetime | None
    disabled_at: datetime | None

    @field_validator("endpoint_ref")
    @classmethod
    def endpoint_ref_must_not_contain_secret(cls, value: str | None) -> str | None:
        """Reject endpoint references that appear to contain credentials."""
        if value is not None:
            _reject_secret_like_text(value)
        return value

    @field_validator("config")
    @classmethod
    def config_must_not_contain_secrets(cls, value: dict[str, Any]) -> dict[str, Any]:
        """Reject secret-like keys recursively."""
        _reject_secret_like_config(value)
        return value

    @model_validator(mode="after")
    def stdio_must_not_contain_shell_fragments(self) -> "MCPServerRecord":
        """Reject shell control markers for stdio transports."""
        if self.transport_type == "stdio":
            values = [self.endpoint_ref or ""]
            values.extend(_string_values(self.config))
            if any(contains_shell_control_chars(value) for value in values):
                raise ValueError("stdio MCP config must not contain shell control characters")
        return self


class MCPToolDescriptor(BaseModel):
    """A normalized MCP tool descriptor at the AION boundary."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    description: str
    input_schema: dict[str, Any]
    output_schema: dict[str, Any] | None = None
    annotations: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("metadata")
    @classmethod
    def metadata_must_not_contain_secrets(cls, value: dict[str, Any]) -> dict[str, Any]:
        """Reject secret-like metadata keys."""
        _reject_secret_like_config(value)
        return value


class MCPCapabilityMapping(BaseModel):
    """Mapping from an MCP tool to an AION capability."""

    model_config = ConfigDict(extra="forbid")

    mapping_id: str = Field(min_length=1)
    mcp_server_id: str = Field(min_length=1)
    mcp_tool_name: str = Field(min_length=1)
    capability_id: str = Field(min_length=1)
    module_id: str = Field(min_length=1)
    risk_level: MCPRiskLevel
    status: MCPMappingStatus
    input_schema: dict[str, Any]
    output_schema: dict[str, Any]
    permissions_required: list[str]
    memory_read_scopes: list[str]
    memory_write_scopes: list[str]
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None
    updated_at: datetime | None
    disabled_at: datetime | None

    @field_validator("metadata")
    @classmethod
    def mapping_metadata_must_not_contain_secrets(
        cls,
        value: dict[str, Any],
    ) -> dict[str, Any]:
        """Reject secret-like mapping metadata."""
        _reject_secret_like_config(value)
        return value


class MCPServerRegistrationRequest(BaseModel):
    """Request to register an MCP server boundary."""

    model_config = ConfigDict(extra="forbid")

    server: MCPServerRecord
    activate: bool = False
    discover_tools: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


class MCPSyncRequest(BaseModel):
    """Request to discover and optionally map MCP tools."""

    model_config = ConfigDict(extra="forbid")

    mcp_server_id: str = Field(min_length=1)
    dry_run: bool = True
    auto_register_capabilities: bool = False
    default_risk_level: MCPRiskLevel = "medium"
    default_permissions_required: list[str] = Field(default_factory=list)
    owner_scope: list[str] = Field(min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)


class MCPSyncResponse(BaseModel):
    """Result of MCP tool discovery and mapping."""

    model_config = ConfigDict(extra="forbid")

    sync_id: str
    mcp_server_id: str
    dry_run: bool
    discovered_tools: int = Field(ge=0)
    mapped_capabilities: int = Field(ge=0)
    skipped: int = Field(ge=0)
    failed: int = Field(ge=0)
    mappings: list[MCPCapabilityMapping]
    errors: list[dict[str, Any]]
    status: MCPSyncStatus
    reason: str | None
    created_at: datetime


class MCPInvocationRequest(BaseModel):
    """Request to invoke or dry-run an MCP-backed capability."""

    model_config = ConfigDict(extra="forbid")

    mcp_invocation_id: str | None = None
    invocation_id: str | None = None
    mcp_server_id: str
    mcp_tool_name: str
    capability_id: str
    trace_id: str | None
    execution_id: str | None
    step_run_id: str | None
    actor_id: str | None
    workspace_id: str | None
    mode: MCPInvocationMode = "dry_run"
    payload: dict[str, Any]
    approval_present: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


class MCPInvocationResult(BaseModel):
    """Result of an MCP-backed capability invocation."""

    model_config = ConfigDict(extra="forbid")

    mcp_invocation_id: str
    invocation_id: str | None
    mcp_server_id: str
    mcp_tool_name: str
    capability_id: str
    status: MCPInvocationStatus
    output: dict[str, Any]
    error: dict[str, Any]
    latency_ms: int | None = Field(default=None, ge=0)
    policy_decision_id: str | None
    created_at: datetime


class MCPServerHealth(BaseModel):
    """Health result for an MCP server boundary."""

    model_config = ConfigDict(extra="forbid")

    mcp_server_id: str
    status: MCPServerHealthStatus
    latency_ms: int | None = Field(default=None, ge=0)
    details: dict[str, Any] = Field(default_factory=dict)
    checked_at: datetime


class MCPAdapterStatus(BaseModel):
    """Process-local status for the MCP adapter boundary."""

    model_config = ConfigDict(extra="forbid")

    adapter_name: str
    enabled: bool
    package_available: bool
    network_allowed: bool
    stdio_allowed: bool
    reason: str | None
    metadata: dict[str, Any] = Field(default_factory=dict)


def contains_shell_control_chars(value: str) -> bool:
    """Return whether a string contains blocked shell control markers."""
    return any(marker in value for marker in _SHELL_CONTROL_MARKERS)


def _reject_secret_like_config(value: object) -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            normalized = str(key).lower().replace("-", "_")
            if normalized in _SECRET_KEYS:
                raise ValueError("config must not contain secret-like keys")
            _reject_secret_like_config(nested)
    elif isinstance(value, list):
        for item in value:
            _reject_secret_like_config(item)


def _reject_secret_like_text(value: str) -> None:
    normalized = value.lower().replace("-", "_")
    if any(marker in normalized for marker in _SECRET_MARKERS):
        raise ValueError("endpoint_ref must not contain secret-like values")


def _string_values(value: object) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        return [item for nested in value.values() for item in _string_values(nested)]
    if isinstance(value, list):
        return [item for nested in value for item in _string_values(nested)]
    return []
