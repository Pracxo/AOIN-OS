"""Typed SDK errors mapped from AION public API error responses."""

from __future__ import annotations

from typing import Any, Self, cast


class AIONSDKError(Exception):
    """Base SDK exception."""


class AIONHTTPError(AIONSDKError):
    """Raised for non-AION HTTP failures or transport errors."""

    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class AIONAPIError(AIONSDKError):
    """Raised for AIONErrorResponse payloads."""

    def __init__(
        self,
        message: str,
        *,
        code: str,
        category: str,
        detail: dict[str, Any] | None = None,
        trace_id: str | None = None,
        correlation_id: str | None = None,
        request_id: str | None = None,
        retryable: bool = False,
        status_code: int | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.category = category
        self.message = message
        self.detail = detail or {}
        self.trace_id = trace_id
        self.correlation_id = correlation_id
        self.request_id = request_id
        self.retryable = retryable
        self.status_code = status_code

    @classmethod
    def from_payload(cls, payload: dict[str, Any], *, status_code: int) -> Self:
        error = payload.get("error")
        if not isinstance(error, dict):
            return cast(
                Self,
                AIONHTTPError(
                    f"AION API returned HTTP {status_code}",
                    status_code=status_code,
                ),
            )
        message = str(error.get("message") or "AION API error")
        code = str(error.get("code") or "AION_UNKNOWN_ERROR")
        category = str(error.get("category") or "internal")
        detail = error.get("detail")
        subclass = _error_subclass(category, code, status_code)
        return cast(
            Self,
            subclass(
                message,
                code=code,
                category=category,
                detail=detail if isinstance(detail, dict) else {},
                trace_id=_optional_string(error.get("trace_id")),
                correlation_id=_optional_string(error.get("correlation_id")),
                request_id=_optional_string(error.get("request_id")),
                retryable=bool(error.get("retryable", False)),
                status_code=status_code,
            ),
        )


class AIONValidationError(AIONAPIError):
    """Validation or contract error."""


class AIONPolicyDeniedError(AIONAPIError):
    """Policy denied the request."""


class AIONAutonomyDeniedError(AIONAPIError):
    """Autonomy governor denied the request."""


class AIONApprovalRequiredError(AIONAPIError):
    """A human approval checkpoint is required."""


class AIONConflictError(AIONAPIError):
    """Conflict or idempotency conflict."""


class AIONNotFoundError(AIONAPIError):
    """Resource was not found."""


class AIONDependencyUnavailableError(AIONAPIError):
    """Dependency, timeout, or unavailable API error."""


def _optional_string(value: object) -> str | None:
    return value if isinstance(value, str) and value else None


def _error_subclass(category: str, code: str, status_code: int) -> type[AIONAPIError]:
    normalized = category.lower()
    normalized_code = code.upper()
    if normalized in {"validation", "contract"} or status_code == 422:
        return AIONValidationError
    if normalized in {"policy", "authorization", "authentication"} or status_code == 403:
        return AIONPolicyDeniedError
    if normalized == "autonomy":
        return AIONAutonomyDeniedError
    if normalized == "approval" or "APPROVAL" in normalized_code:
        return AIONApprovalRequiredError
    if normalized in {"conflict", "idempotency"} or status_code == 409:
        return AIONConflictError
    if normalized == "not_found" or status_code == 404:
        return AIONNotFoundError
    if normalized in {"dependency", "unavailable", "timeout"} or status_code in {408, 503, 504}:
        return AIONDependencyUnavailableError
    return AIONAPIError

