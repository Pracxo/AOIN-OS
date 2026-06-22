"""AION-owned API exceptions and sanitization helpers."""

from __future__ import annotations

import re
from typing import Any

from aion_brain.api_support import error_codes
from aion_brain.contracts.api import APIErrorCategory

_SECRET_KEY_FRAGMENTS = (
    "password",
    "secret",
    "token",
    "api_key",
    "apikey",
    "private_key",
    "authorization",
    "credential",
)
_PROVIDER_KEY_FRAGMENTS = ("provider", "adapter_response", "sdk_response")
_RAW_SQL_PATTERN = re.compile(
    r"\b(select|insert|update|delete|drop|alter|create)\b.+\b(from|into|table|where)\b",
    re.IGNORECASE | re.DOTALL,
)
_STACKTRACE_PATTERN = re.compile(r"(traceback|stack trace|File \")", re.IGNORECASE)
_PROVIDER_PATTERN = re.compile(
    r"\b(openai|anthropic|gemini|litellm|temporal|graphiti|turbovec)\b",
    re.IGNORECASE,
)


class AIONException(Exception):
    """Base exception that maps directly to AIONErrorResponse."""

    def __init__(
        self,
        *,
        code: str,
        category: APIErrorCategory,
        message: str,
        detail: dict[str, Any] | None = None,
        retryable: bool = False,
        status_code: int = 500,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.category = category
        self.message = message
        self.detail = sanitize_detail(detail or {})
        self.retryable = retryable
        self.status_code = status_code


class AIONValidationException(AIONException):
    """Validation error raised by AION-owned helpers."""

    def __init__(self, message: str, detail: dict[str, Any] | None = None) -> None:
        super().__init__(
            code=error_codes.AION_VALIDATION_ERROR,
            category="validation",
            message=message,
            detail=detail,
            status_code=422,
        )


class AIONNotFoundException(AIONException):
    """Missing AION resource."""

    def __init__(self, message: str = "AION resource was not found.") -> None:
        super().__init__(
            code=error_codes.AION_NOT_FOUND,
            category="not_found",
            message=message,
            status_code=404,
        )


class AIONConflictException(AIONException):
    """State conflict."""

    def __init__(self, message: str, detail: dict[str, Any] | None = None) -> None:
        super().__init__(
            code=error_codes.AION_CONFLICT,
            category="conflict",
            message=message,
            detail=detail,
            status_code=409,
        )


class AIONPolicyDeniedException(AIONException):
    """Policy denied the requested action."""

    def __init__(self, message: str = "AION policy denied this request.") -> None:
        super().__init__(
            code=error_codes.AION_POLICY_DENIED,
            category="policy",
            message=message,
            status_code=403,
        )


class AIONAutonomyDeniedException(AIONException):
    """Autonomy controls denied the requested action."""

    def __init__(self, message: str = "AION autonomy controls denied this request.") -> None:
        super().__init__(
            code=error_codes.AION_AUTONOMY_DENIED,
            category="autonomy",
            message=message,
            status_code=403,
        )


class AIONApprovalRequiredException(AIONException):
    """Approval is required before the action can continue."""

    def __init__(self, message: str = "AION approval is required.") -> None:
        super().__init__(
            code=error_codes.AION_APPROVAL_REQUIRED,
            category="approval",
            message=message,
            status_code=409,
        )


class AIONUnsupportedOperationException(AIONException):
    """Unsupported API operation."""

    def __init__(self, message: str = "AION does not support this operation.") -> None:
        super().__init__(
            code=error_codes.AION_UNSUPPORTED_OPERATION,
            category="unsupported",
            message=message,
            status_code=400,
        )


class AIONDependencyUnavailableException(AIONException):
    """Dependency or adapter is unavailable."""

    def __init__(self, message: str = "AION dependency is unavailable.") -> None:
        super().__init__(
            code=error_codes.AION_DEPENDENCY_UNAVAILABLE,
            category="dependency",
            message=message,
            retryable=True,
            status_code=503,
        )


class AIONInternalException(AIONException):
    """Internal AION error without public stack traces."""

    def __init__(self, message: str = "An internal AION error occurred.") -> None:
        super().__init__(
            code=error_codes.AION_INTERNAL_ERROR,
            category="internal",
            message=message,
            status_code=500,
        )


def sanitize_detail(value: Any) -> dict[str, Any]:
    """Return a public-safe dictionary representation of error details."""
    sanitized = _sanitize_value(value)
    if isinstance(sanitized, dict):
        return sanitized
    return {"detail": sanitized}


def _sanitize_value(value: Any) -> Any:
    if isinstance(value, dict):
        sanitized: dict[str, Any] = {}
        for key, nested in value.items():
            normalized = str(key).lower().replace("-", "_")
            if any(fragment in normalized for fragment in _SECRET_KEY_FRAGMENTS):
                sanitized["redacted"] = True
            elif any(fragment in normalized for fragment in _PROVIDER_KEY_FRAGMENTS):
                sanitized["redacted"] = True
            else:
                sanitized[str(key)] = _sanitize_value(nested)
        return sanitized
    if isinstance(value, list):
        return [_sanitize_value(item) for item in value]
    if isinstance(value, tuple):
        return [_sanitize_value(item) for item in value]
    if isinstance(value, str):
        return _sanitize_text(value)
    if value is None or isinstance(value, (bool, int, float)):
        return value
    return {"type": "object"}


def _sanitize_text(value: str) -> str:
    if (
        _RAW_SQL_PATTERN.search(value)
        or _STACKTRACE_PATTERN.search(value)
        or _PROVIDER_PATTERN.search(value)
        or any(fragment in value.lower() for fragment in _SECRET_KEY_FRAGMENTS)
    ):
        return "[redacted]"
    return value[:1000]
