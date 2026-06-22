"""Generic API control-surface contracts owned by AION Brain."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

APIErrorCategory = Literal[
    "validation",
    "authentication",
    "authorization",
    "policy",
    "autonomy",
    "risk",
    "approval",
    "not_found",
    "conflict",
    "idempotency",
    "rate_limit",
    "dependency",
    "unavailable",
    "timeout",
    "internal",
    "unsupported",
    "contract",
]

SortOrder = Literal["asc", "desc"]
FilterOperator = Literal[
    "equals",
    "not_equals",
    "in",
    "not_in",
    "exists",
    "contains",
    "starts_with",
    "ends_with",
    "gte",
    "lte",
]

HygieneStatus = Literal["passed", "failed"]
SECRET_KEY_FRAGMENTS = (
    "password",
    "secret",
    "token",
    "api_key",
    "apikey",
    "private_key",
    "authorization",
    "credential",
)


class AIONError(BaseModel):
    """Standard public API error contract."""

    model_config = ConfigDict(extra="forbid")

    code: str = Field(min_length=1)
    category: APIErrorCategory
    message: str = Field(min_length=1)
    detail: dict[str, Any] = Field(default_factory=dict)
    trace_id: str | None = None
    correlation_id: str | None = None
    request_id: str | None = None
    retryable: bool = False
    created_at: datetime

    @field_validator("detail")
    @classmethod
    def reject_secret_detail(cls, value: dict[str, Any]) -> dict[str, Any]:
        """Keep public error details free of secret-like keys."""
        _reject_secret_keys(value)
        return value


class AIONErrorResponse(BaseModel):
    """Standard public API error response."""

    model_config = ConfigDict(extra="forbid")

    error: AIONError


class AIONSuccessEnvelope(BaseModel):
    """Optional success envelope for new API support endpoints."""

    model_config = ConfigDict(extra="forbid")

    data: Any
    trace_id: str | None = None
    correlation_id: str | None = None
    request_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class AIONPageRequest(BaseModel):
    """Generic pagination request contract."""

    model_config = ConfigDict(extra="forbid")

    limit: int = Field(default=50, ge=1, le=500)
    cursor: str | None = None
    sort_by: str | None = None
    sort_order: SortOrder = "desc"

    @field_validator("cursor")
    @classmethod
    def validate_cursor(cls, value: str | None) -> str | None:
        """Reject cursor strings outside URL-safe base64 JSON form."""
        if value is None:
            return None
        if not value or any(character not in _CURSOR_CHARS for character in value):
            raise ValueError("cursor contains unsafe characters")
        return value

    @field_validator("sort_by")
    @classmethod
    def validate_sort_by(cls, value: str | None) -> str | None:
        """Restrict sort fields to safe contract field names."""
        if value is not None:
            _validate_safe_path(value, "sort_by")
        return value


class AIONPageInfo(BaseModel):
    """Pagination metadata returned with an AION page."""

    model_config = ConfigDict(extra="forbid")

    limit: int = Field(ge=1, le=500)
    next_cursor: str | None = None
    previous_cursor: str | None = None
    has_next: bool
    total_count: int | None = Field(default=None, ge=0)


class AIONPage(BaseModel):
    """Generic page of public AION contract items."""

    model_config = ConfigDict(extra="forbid")

    items: list[Any]
    page: AIONPageInfo
    trace_id: str | None = None
    correlation_id: str | None = None
    request_id: str | None = None


class AIONFilter(BaseModel):
    """Generic safe filter expression for in-memory helpers and SDKs."""

    model_config = ConfigDict(extra="forbid")

    field: str = Field(min_length=1)
    operator: FilterOperator
    value: Any | None = None
    values: list[Any] = Field(default_factory=list)

    @field_validator("field")
    @classmethod
    def validate_field(cls, value: str) -> str:
        """Reject SQL fragments, eval-like syntax, and unsafe paths."""
        _validate_safe_path(value, "field")
        return value


class AIONSort(BaseModel):
    """Generic safe sort expression."""

    model_config = ConfigDict(extra="forbid")

    field: str = Field(min_length=1)
    order: SortOrder = "desc"

    @field_validator("field")
    @classmethod
    def validate_field(cls, value: str) -> str:
        """Reject unsafe sort fields."""
        _validate_safe_path(value, "field")
        return value


class RequestContext(BaseModel):
    """Per-request metadata extracted by API middleware."""

    model_config = ConfigDict(extra="forbid")

    request_id: str
    trace_id: str | None = None
    correlation_id: str | None = None
    idempotency_key: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    method: str
    path: str
    route_name: str | None = None
    started_at: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("metadata")
    @classmethod
    def reject_secret_metadata(cls, value: dict[str, Any]) -> dict[str, Any]:
        """Keep request context metadata sanitized."""
        _reject_secret_keys(value)
        return value


class APIRequestRecord(BaseModel):
    """Persisted safe request audit record."""

    model_config = ConfigDict(extra="forbid")

    request_id: str
    trace_id: str | None = None
    correlation_id: str | None = None
    idempotency_key: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    method: str
    path: str
    route_name: str | None = None
    status_code: int | None = None
    duration_ms: int | None = None
    client_host: str | None = None
    user_agent: str | None = None
    error_code: str | None = None
    error_category: str | None = None
    request_metadata: dict[str, Any] = Field(default_factory=dict)
    response_metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None
    completed_at: datetime | None = None

    @field_validator("request_metadata", "response_metadata")
    @classmethod
    def reject_secret_metadata(cls, value: dict[str, Any]) -> dict[str, Any]:
        """Keep audit metadata free of secret-like keys."""
        _reject_secret_keys(value)
        return value


class OpenAPIHygieneReport(BaseModel):
    """OpenAPI contract hygiene result."""

    model_config = ConfigDict(extra="forbid")

    report_id: str
    status: HygieneStatus
    violations: list[dict[str, Any]]
    route_count: int = Field(ge=0)
    checked_at: datetime


class BrainAPIRequestList(BaseModel):
    """Query contract for API request audit records."""

    model_config = ConfigDict(extra="forbid")

    trace_id: str | None = None
    correlation_id: str | None = None
    limit: int = Field(default=50, ge=1, le=500)


_CURSOR_CHARS = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_=")
_SAFE_PATH_CHARS = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_.-")
_UNSAFE_FIELD_TOKENS = (
    " ",
    ";",
    "'",
    '"',
    "(",
    ")",
    "[",
    "]",
    "{",
    "}",
    "/",
    "\\",
    "*",
    "+",
    "=",
    "<",
    ">",
    "|",
    "&",
    "$",
    "`",
)


def _validate_safe_path(value: str, field_name: str) -> None:
    if (
        not value
        or value.startswith(".")
        or value.endswith(".")
        or ".." in value
        or any(character not in _SAFE_PATH_CHARS for character in value)
        or any(token in value for token in _UNSAFE_FIELD_TOKENS)
    ):
        raise ValueError(f"{field_name} must be a safe dotted path")


def _reject_secret_keys(value: object) -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            normalized = str(key).lower().replace("-", "_")
            if any(fragment in normalized for fragment in SECRET_KEY_FRAGMENTS):
                raise ValueError("metadata must not contain secret-like keys")
            _reject_secret_keys(nested)
    elif isinstance(value, list):
        for item in value:
            _reject_secret_keys(item)
