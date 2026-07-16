"""Stable reason-code registry for disabled production-auth evidence."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any

REASON_CODE_REGISTRY_VERSION = "production-auth-reason-codes/v1"


@dataclass(frozen=True, slots=True)
class ProductionAuthReasonCode:
    """Immutable production-auth reason-code descriptor."""

    code: str
    summary: str


_REASON_CODES: tuple[ProductionAuthReasonCode, ...] = (
    ProductionAuthReasonCode(
        "production_auth_runtime_disabled",
        "Production-auth runtime remains disabled.",
    ),
    ProductionAuthReasonCode(
        "runtime_enablement_guard_locked",
        "Runtime enablement guard remains locked.",
    ),
    ProductionAuthReasonCode(
        "authorization_scope_implementation_only",
        "Authorization permits implementation stabilization only.",
    ),
    ProductionAuthReasonCode(
        "endpoint_surface_absent",
        "Public production-auth endpoint surface is absent.",
    ),
    ProductionAuthReasonCode(
        "protected_material_storage_absent",
        "Credential, token, cookie, and session storage are absent.",
    ),
    ProductionAuthReasonCode(
        "external_identity_provider_absent",
        "External identity-provider runtime is absent.",
    ),
)

REQUIRED_REASON_CODES: tuple[str, ...] = tuple(item.code for item in _REASON_CODES)
REASON_CODE_REGISTRY = MappingProxyType({item.code: item for item in _REASON_CODES})


def get_reason_code(code: str) -> ProductionAuthReasonCode:
    """Return one registered reason-code descriptor."""

    try:
        return REASON_CODE_REGISTRY[code]
    except KeyError as exc:
        raise ValueError(f"unknown production-auth reason code: {code}") from exc


def validate_reason_codes(codes: list[str] | tuple[str, ...]) -> tuple[str, ...]:
    """Validate and normalize reason codes into registry order."""

    if not codes:
        raise ValueError("reason_codes cannot be empty")
    seen: set[str] = set()
    for code in codes:
        get_reason_code(code)
        if code in seen:
            raise ValueError(f"duplicate production-auth reason code: {code}")
        seen.add(code)
    return tuple(code for code in REQUIRED_REASON_CODES if code in seen)


def reason_code_registry_payload() -> dict[str, Any]:
    """Return a deterministic serializable registry view."""

    return {
        "reason_code_registry_version": REASON_CODE_REGISTRY_VERSION,
        "reason_codes": [
            {"code": item.code, "summary": item.summary}
            for item in _REASON_CODES
        ],
    }


__all__ = [
    "PRODUCTION_AUTH_REASON_CODES",
    "REASON_CODE_REGISTRY",
    "REASON_CODE_REGISTRY_VERSION",
    "REQUIRED_REASON_CODES",
    "ProductionAuthReasonCode",
    "get_reason_code",
    "reason_code_registry_payload",
    "validate_reason_codes",
]

PRODUCTION_AUTH_REASON_CODES = REQUIRED_REASON_CODES
