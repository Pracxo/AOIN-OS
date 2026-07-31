"""Redacted model-gateway observability and health snapshots."""

from __future__ import annotations

from datetime import datetime

from aion_brain.contracts.model_gateway import (
    ModelGatewayHealthSnapshot,
    ModelGatewayObservabilitySnapshot,
)


def observability_snapshot(
    *,
    snapshot_id: str,
    session_id: str,
    event_counters: dict[str, int],
    health_state: str,
    audit_chain_head: str,
    created_at: datetime,
) -> ModelGatewayObservabilitySnapshot:
    """Build a redacted observability snapshot."""

    return ModelGatewayObservabilitySnapshot(
        snapshot_id=snapshot_id,
        session_id=session_id,
        event_counters=event_counters,
        health_state=health_state,
        audit_chain_head=audit_chain_head,
        created_at=created_at,
    )


def health_snapshot(
    *,
    health_id: str,
    health_state: str,
    created_at: datetime,
    authorization_valid: bool = True,
    secure_runtime_binding_valid: bool = True,
    parent_kill_switch_clear: bool = True,
    provider_registry_exact: bool = True,
    model_registry_exact: bool = True,
    reference_provider_available: bool = True,
    budgets_valid: bool = True,
) -> ModelGatewayHealthSnapshot:
    """Build a readiness health snapshot."""

    return ModelGatewayHealthSnapshot(
        health_id=health_id,
        health_state=health_state,
        authorization_valid=authorization_valid,
        secure_runtime_binding_valid=secure_runtime_binding_valid,
        parent_kill_switch_clear=parent_kill_switch_clear,
        provider_registry_exact=provider_registry_exact,
        model_registry_exact=model_registry_exact,
        reference_provider_available=reference_provider_available,
        budgets_valid=budgets_valid,
        created_at=created_at,
    )
