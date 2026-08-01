"""Authorization envelope construction for the controlled local console."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import timedelta
from typing import Any

from aion_brain.contracts.operator_console_integration import (
    ALL_RESOURCE_LIMITS,
    APPROVAL_RECORD_ID,
    AUTHORIZATION_SCOPE,
    AUTHORIZATION_TRANSACTION_ID,
    LOCAL_CONFIRMATION_TEXT,
    LOOPBACK_BIND_HOST,
    OperatorConsoleComponentBinding,
    OperatorConsoleIntegrationAuthorizationEnvelope,
    OperatorConsoleStaticAssetManifest,
    default_route_manifest,
    fingerprint_text,
    resource_limits_fingerprint,
    security_headers_fingerprint,
    utc_now,
)


def validate_operator_console_authorization_inputs(
    *,
    program_ledger: Mapping[str, Any],
    authorization_ledger: Mapping[str, Any],
    authorization_example: Mapping[str, Any],
) -> None:
    """Fail closed unless AION-236-SRI-0004 remains the sole active SRI authority."""

    for payload in (program_ledger, authorization_ledger, authorization_example):
        if payload.get("active_sri_implementation_authorization") != AUTHORIZATION_TRANSACTION_ID:
            raise ValueError("active SRI authorization mismatch")
        if payload.get("active_sri_implementation_authorization_count") != 1:
            raise ValueError("active SRI authorization count mismatch")
        if payload.get("active_sri_implementation_task") != "AION-237":
            raise ValueError("active SRI task mismatch")
        if payload.get("formal_closeout_task") != "AION-238":
            raise ValueError("formal closeout task mismatch")
        if payload.get("production_runtime_authorized") is not False:
            raise ValueError("production runtime must remain unauthorized")
        if payload.get("v02_release_ready") is not False:
            raise ValueError("v0.2 readiness must remain false")

    if authorization_example.get("authorization_transaction_id") != AUTHORIZATION_TRANSACTION_ID:
        raise ValueError("authorization transaction mismatch")
    if authorization_example.get("approval_record_id") != APPROVAL_RECORD_ID:
        raise ValueError("approval record mismatch")
    if authorization_example.get("authorization_scope") != AUTHORIZATION_SCOPE:
        raise ValueError("authorization scope mismatch")
    if authorization_example.get("authorization_active") is not True:
        raise ValueError("authorization must remain active")
    if authorization_example.get("authorization_consumed") is not False:
        raise ValueError("authorization must not be consumed by AION-237")
    if authorization_example.get("authorization_expired") is not False:
        raise ValueError("authorization must not expire before AION-238")
    if authorization_example.get("authorization_reusable") is not False:
        raise ValueError("authorization must not become reusable")

    limits = authorization_example.get("operator_console_resource_limits")
    if limits != ALL_RESOURCE_LIMITS:
        raise ValueError("operator console resource limits mismatch")


def build_authorization_envelope(
    *,
    console_session_id: str,
    component_binding: OperatorConsoleComponentBinding,
    operator_identity_fingerprint: str,
    actor_context_fingerprint: str,
    bound_port: int,
    static_asset_manifest: OperatorConsoleStaticAssetManifest,
) -> OperatorConsoleIntegrationAuthorizationEnvelope:
    """Create an AION-236 authorized same-origin loopback console envelope."""

    created_at = utc_now()
    return OperatorConsoleIntegrationAuthorizationEnvelope(
        console_session_id=console_session_id,
        component_binding=component_binding,
        operator_identity_fingerprint=operator_identity_fingerprint,
        actor_context_fingerprint=actor_context_fingerprint,
        bound_host=LOOPBACK_BIND_HOST,
        bound_port=bound_port,
        bound_origin=f"http://{LOOPBACK_BIND_HOST}:{bound_port}",
        route_manifest_fingerprint=default_route_manifest().manifest_fingerprint or "",
        static_asset_manifest_fingerprint=static_asset_manifest.manifest_fingerprint or "",
        security_headers_fingerprint=security_headers_fingerprint(),
        resource_limits_fingerprint=resource_limits_fingerprint(),
        created_at=created_at,
        expires_at=created_at + timedelta(seconds=ALL_RESOURCE_LIMITS["maximum_session_seconds"]),
        idle_expires_at=created_at + timedelta(seconds=ALL_RESOURCE_LIMITS["maximum_idle_seconds"]),
        confirmation_fingerprint=fingerprint_text("confirmation", LOCAL_CONFIRMATION_TEXT),
    )
