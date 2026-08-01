"""Redacted AION-237 pilot evidence helpers."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from aion_brain.contracts.operator_console_integration import (
    AUTHORIZATION_TRANSACTION_ID,
    LOOPBACK_BIND_HOST,
    PROHIBITED_COUNTER_NAMES,
    ZERO_FINGERPRINT,
    OperatorConsoleEvidenceBundle,
    operator_console_fingerprint,
)

PILOT_ID = "AION-237-controlled-operator-console-integrated-local-runtime-pilot"


def prohibited_counter_zero_map() -> dict[str, int]:
    return {name: 0 for name in PROHIBITED_COUNTER_NAMES}


def build_evidence_bundle(
    *,
    secure_runtime_component_binding_fingerprint: str,
    model_gateway_component_binding_fingerprint: str,
    capability_runtime_component_binding_fingerprint: str,
    route_manifest_fingerprint: str,
    static_asset_manifest_fingerprint: str,
    security_headers_fingerprint: str,
    counters: Mapping[str, int | bool],
    listener_audit_chain_head: str,
    console_audit_chain_head: str,
    secure_runtime_receipt_chain_head: str = ZERO_FINGERPRINT,
    model_gateway_audit_chain_head: str = ZERO_FINGERPRINT,
    capability_runtime_receipt_chain_head: str = ZERO_FINGERPRINT,
) -> OperatorConsoleEvidenceBundle:
    return OperatorConsoleEvidenceBundle(
        pilot_id=PILOT_ID,
        authorization_id=AUTHORIZATION_TRANSACTION_ID,
        bind_host=LOOPBACK_BIND_HOST,
        secure_runtime_component_binding_fingerprint=secure_runtime_component_binding_fingerprint,
        model_gateway_component_binding_fingerprint=model_gateway_component_binding_fingerprint,
        capability_runtime_component_binding_fingerprint=capability_runtime_component_binding_fingerprint,
        route_manifest_fingerprint=route_manifest_fingerprint,
        static_asset_manifest_fingerprint=static_asset_manifest_fingerprint,
        security_headers_fingerprint=security_headers_fingerprint,
        counters=dict(counters),
        prohibited_effect_counters=prohibited_counter_zero_map(),
        listener_audit_chain_head=listener_audit_chain_head,
        console_audit_chain_head=console_audit_chain_head,
        secure_runtime_receipt_chain_head=secure_runtime_receipt_chain_head,
        model_gateway_audit_chain_head=model_gateway_audit_chain_head,
        capability_runtime_receipt_chain_head=capability_runtime_receipt_chain_head,
    )


def evidence_report_fingerprint(payload: Mapping[str, Any]) -> str:
    redacted = {key: value for key, value in payload.items() if key != "report_fingerprint"}
    return operator_console_fingerprint(redacted)
