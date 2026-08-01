"""Redacted view-model helpers for the local Operator Console."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from aion_brain.contracts.operator_console_integration import (
    AUTHORIZATION_TRANSACTION_ID,
    IMPLEMENTATION_TASK,
    ZERO_FINGERPRINT,
    OperatorConsoleActionKind,
    OperatorConsoleActionProjection,
    OperatorConsoleHealthProjection,
    OperatorConsoleHttpDisposition,
    OperatorConsoleIntegrityStatus,
    OperatorConsoleReceiptProjection,
    OperatorConsoleSessionStatus,
    OperatorConsoleStatusProjection,
    fingerprint_mapping,
)


def status_projection(
    *,
    console_session_state: OperatorConsoleSessionStatus,
    kill_switch_state: str,
    active_request_count: int,
    receipt_count: int,
    audit_count: int,
) -> OperatorConsoleStatusProjection:
    return OperatorConsoleStatusProjection(
        console_session_state=console_session_state,
        secure_runtime_state="pre_authenticated_local_operator_session",
        model_gateway_state="deterministic_reference_simulation_available",
        capability_runtime_state="reference_capability_runtime_available",
        kill_switch_state=kill_switch_state,
        active_request_count=active_request_count,
        receipt_count=receipt_count,
        audit_count=audit_count,
        production_flags={
            "production_runtime_authorized": False,
            "production_write_execution_enabled": False,
            "production_memory_write_enabled": False,
            "production_policy_mutation_enabled": False,
            "production_exposure": False,
        },
    )


def health_projection(
    *,
    session_valid: bool,
    nonce_valid: bool,
    kill_switch_clear: bool,
    listener_active: bool,
) -> OperatorConsoleHealthProjection:
    return OperatorConsoleHealthProjection(
        ready=session_valid and nonce_valid and listener_active,
        component_availability={
            "secure_runtime": True,
            "model_gateway": True,
            "capability_runtime": True,
            "operator_console": True,
        },
        authorization_exact=True,
        session_valid=session_valid,
        nonce_valid=nonce_valid,
        host_policy_valid=True,
        origin_policy_valid=True,
        resource_budget_valid=True,
        kill_switch_clear=kill_switch_clear,
        listener_active=listener_active,
        integrity_status=OperatorConsoleIntegrityStatus.passed,
    )


def action_projection(
    *,
    action_kind: OperatorConsoleActionKind,
    request_id: str,
    transient_output: Any,
    output_fingerprint: str,
    output_byte_count: int,
    writes_applied: int = 0,
) -> OperatorConsoleActionProjection:
    return OperatorConsoleActionProjection(
        action_kind=action_kind,
        request_id=request_id,
        status="accepted",
        output_fingerprint=output_fingerprint,
        output_byte_count=output_byte_count,
        receipt_fingerprint=fingerprint_mapping(
            "receipt", {"authorization": AUTHORIZATION_TRANSACTION_ID, "request_id": request_id}
        ),
        provenance_fingerprint=fingerprint_mapping(
            "provenance", {"task": IMPLEMENTATION_TASK, "request_id": request_id}
        ),
        validation_fingerprint=fingerprint_mapping(
            "validation", {"request_id": request_id, "trusted": False}
        ),
        transient_output=transient_output,
        writes_applied=writes_applied,
    )


def receipt_projection(
    *,
    request_id: str,
    action_kind: OperatorConsoleActionKind,
    prior_receipt_fingerprint: str = ZERO_FINGERPRINT,
    disposition: OperatorConsoleHttpDisposition = OperatorConsoleHttpDisposition.accepted,
) -> OperatorConsoleReceiptProjection:
    receipt_fingerprint = fingerprint_mapping(
        "receipt-projection",
        {"request_id": request_id, "action": action_kind.value, "prior": prior_receipt_fingerprint},
    )
    return OperatorConsoleReceiptProjection(
        request_id=request_id,
        receipt_fingerprint=receipt_fingerprint,
        prior_receipt_fingerprint=prior_receipt_fingerprint,
        action_kind=action_kind,
        disposition=disposition,
    )


def redacted_projection_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    return {str(key): value for key, value in sorted(payload.items())}
