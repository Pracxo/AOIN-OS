"""Stable AION API error taxonomy."""

from typing import Any

from aion_brain.contracts.api import APIErrorCategory

AION_VALIDATION_ERROR = "AION_VALIDATION_ERROR"
AION_CONTRACT_VALIDATION_ERROR = "AION_CONTRACT_VALIDATION_ERROR"
AION_NOT_FOUND = "AION_NOT_FOUND"
AION_CONFLICT = "AION_CONFLICT"
AION_IDEMPOTENCY_CONFLICT = "AION_IDEMPOTENCY_CONFLICT"
AION_POLICY_DENIED = "AION_POLICY_DENIED"
AION_AUTONOMY_DENIED = "AION_AUTONOMY_DENIED"
AION_RISK_BLOCKED = "AION_RISK_BLOCKED"
AION_APPROVAL_REQUIRED = "AION_APPROVAL_REQUIRED"
AION_UNSUPPORTED_OPERATION = "AION_UNSUPPORTED_OPERATION"
AION_DEPENDENCY_UNAVAILABLE = "AION_DEPENDENCY_UNAVAILABLE"
AION_ADAPTER_UNAVAILABLE = "AION_ADAPTER_UNAVAILABLE"
AION_TIMEOUT = "AION_TIMEOUT"
AION_INTERNAL_ERROR = "AION_INTERNAL_ERROR"
AION_ROUTE_NOT_FOUND = "AION_ROUTE_NOT_FOUND"
AION_METHOD_NOT_ALLOWED = "AION_METHOD_NOT_ALLOWED"
AION_REQUEST_TOO_LARGE = "AION_REQUEST_TOO_LARGE"
AION_RATE_LIMITED = "AION_RATE_LIMITED"
AION_UNAUTHORIZED = "AION_UNAUTHORIZED"
AION_FORBIDDEN = "AION_FORBIDDEN"

ERROR_CODE_TAXONOMY: dict[str, dict[str, Any]] = {
    AION_VALIDATION_ERROR: {"category": "validation", "retryable": False},
    AION_CONTRACT_VALIDATION_ERROR: {"category": "contract", "retryable": False},
    AION_NOT_FOUND: {"category": "not_found", "retryable": False},
    AION_CONFLICT: {"category": "conflict", "retryable": False},
    AION_IDEMPOTENCY_CONFLICT: {"category": "idempotency", "retryable": False},
    AION_POLICY_DENIED: {"category": "policy", "retryable": False},
    AION_AUTONOMY_DENIED: {"category": "autonomy", "retryable": False},
    AION_RISK_BLOCKED: {"category": "risk", "retryable": False},
    AION_APPROVAL_REQUIRED: {"category": "approval", "retryable": False},
    AION_UNSUPPORTED_OPERATION: {"category": "unsupported", "retryable": False},
    AION_DEPENDENCY_UNAVAILABLE: {"category": "dependency", "retryable": True},
    AION_ADAPTER_UNAVAILABLE: {"category": "unavailable", "retryable": True},
    AION_TIMEOUT: {"category": "timeout", "retryable": True},
    AION_INTERNAL_ERROR: {"category": "internal", "retryable": False},
    AION_ROUTE_NOT_FOUND: {"category": "not_found", "retryable": False},
    AION_METHOD_NOT_ALLOWED: {"category": "unsupported", "retryable": False},
    AION_REQUEST_TOO_LARGE: {"category": "validation", "retryable": False},
    AION_RATE_LIMITED: {"category": "rate_limit", "retryable": True},
    AION_UNAUTHORIZED: {"category": "authentication", "retryable": False},
    AION_FORBIDDEN: {"category": "authorization", "retryable": False},
}


def category_for_code(code: str) -> APIErrorCategory:
    """Return the stable category for an error code."""
    category = ERROR_CODE_TAXONOMY.get(code, ERROR_CODE_TAXONOMY[AION_INTERNAL_ERROR])["category"]
    return str(category)  # type: ignore[return-value]


def retryable_for_code(code: str) -> bool:
    """Return whether clients may retry this error code."""
    retryable = ERROR_CODE_TAXONOMY.get(code, ERROR_CODE_TAXONOMY[AION_INTERNAL_ERROR])["retryable"]
    return bool(retryable)
