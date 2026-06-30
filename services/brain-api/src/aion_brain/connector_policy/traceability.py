"""Connector policy traceability evidence."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from aion_brain.connector_policy.catalog import DENIED_ACTION_KEYS, PREVIEW_ACTION_KEYS
from aion_brain.contracts.connector_policy import ConnectorPolicyTraceabilityRecord, utc_now
from aion_brain.dialogue._shared import emit_telemetry


class ConnectorPolicyTraceabilityService:
    """Build deterministic connector policy traceability records."""

    def __init__(self, *, telemetry_service: object | None = None) -> None:
        self._telemetry_service = telemetry_service

    def query(
        self,
        payload: dict[str, Any],
        owner_scope: list[str],
    ) -> list[ConnectorPolicyTraceabilityRecord]:
        """Return traceability rows without reading connector runtime state."""

        connector_key = str(payload.get("connector_key") or "mock.local.preview")
        requested = payload.get("action_key")
        action_keys = (
            [str(requested)]
            if isinstance(requested, str) and requested.strip()
            else [
                "connector_policy.catalog.read",
                "connector_policy.matrix.read",
                "connector_policy.dry_run",
                "connector_policy.traceability.read",
            ]
        )
        records = [
            _record(connector_key, action_key, owner_scope)
            for action_key in action_keys
            if action_key in PREVIEW_ACTION_KEYS or action_key in DENIED_ACTION_KEYS
        ]
        emit_telemetry(
            self._telemetry_service,
            event_type="connector_policy_traceability_queried",
            node_type="connector_policy_traceability",
            node_id=f"connector-policy-traceability-{uuid4().hex}",
            intensity=0.5,
            trace_id=str(payload.get("trace_id") or "connector-policy-traceability-local"),
            payload={"record_count": len(records), "runtime_allowed": False},
        )
        return records


def _record(
    connector_key: str,
    action_key: str,
    owner_scope: list[str],
) -> ConnectorPolicyTraceabilityRecord:
    denied = action_key in DENIED_ACTION_KEYS
    return ConnectorPolicyTraceabilityRecord(
        traceability_id=f"connector-policy-traceability-{uuid4().hex}",
        connector_key=connector_key,
        action_key=action_key,
        policy_refs=[
            "docs/connectors/connector-policy-action-catalog.md",
            "docs/connectors/connector-policy-no-go.md",
        ],
        matrix_refs=["docs/connectors/connector-authorization-matrix.md"],
        evidence_refs=[
            "docs/connectors/connector-policy-traceability.md",
            "examples/connectors/connector-policy-traceability.json",
        ],
        dry_run_refs=["docs/connectors/connector-policy-dry-run-gate.md"],
        denial_refs=["docs/connectors/connector-policy-denial-rules.md"] if denied else [],
        audit_refs=["docs/connectors/connector-runtime-audit.md"],
        status="blocked" if denied else "ready",
        metadata={"owner_scope": owner_scope, "runtime_allowed": False},
        created_at=utc_now(),
    )


__all__ = ["ConnectorPolicyTraceabilityService"]
