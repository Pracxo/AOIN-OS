"""Connector policy action catalog."""

from __future__ import annotations

from aion_brain.contracts.connector_policy import (
    ConnectorPolicyAction,
    ConnectorPolicyRiskLevel,
)
from aion_brain.dialogue._shared import emit_telemetry

PREVIEW_ACTION_KEYS = (
    "connector_runtime.status.read",
    "connector_runtime.mock_manifest.validate",
    "connector_runtime.egress.preview",
    "connector_runtime.ingress.preview",
    "connector_runtime.audit.run",
    "connector_simulator.simulate",
    "connector_simulator.replay",
    "connector_simulator.policy_readiness",
    "connector_simulator.status.read",
    "connector_simulator.query",
    "connector_policy.catalog.read",
    "connector_policy.matrix.read",
    "connector_policy.dry_run",
    "connector_policy.traceability.read",
)

DENIED_ACTION_KEYS = (
    "connector.runtime.enable",
    "connector.external.call",
    "connector.credentials.store",
    "connector.tokens.store",
    "connector.activate",
    "connector.route.register",
    "connector.tool.execute",
    "connector.write.execute",
    "connector.provider.call",
)

_ACTION_LABELS = {
    "connector_runtime.status.read": "Connector Runtime Status Read",
    "connector_runtime.mock_manifest.validate": "Mock Manifest Validate",
    "connector_runtime.egress.preview": "Connector Egress Preview",
    "connector_runtime.ingress.preview": "Connector Ingress Preview",
    "connector_runtime.audit.run": "Connector Runtime Audit Run",
    "connector_simulator.simulate": "Connector Simulator Simulate",
    "connector_simulator.replay": "Connector Simulator Replay",
    "connector_simulator.policy_readiness": "Connector Simulator Policy Readiness",
    "connector_simulator.status.read": "Connector Simulator Status Read",
    "connector_simulator.query": "Connector Simulator Query",
    "connector_policy.catalog.read": "Connector Policy Catalog Read",
    "connector_policy.matrix.read": "Connector Policy Matrix Read",
    "connector_policy.dry_run": "Connector Policy Dry Run",
    "connector_policy.traceability.read": "Connector Policy Traceability Read",
}


class ConnectorPolicyCatalogService:
    """Expose a deterministic read-only connector policy action catalog."""

    def __init__(self, *, telemetry_service: object | None = None) -> None:
        self._telemetry_service = telemetry_service

    def list_actions(self, *, include_denied: bool = True) -> list[ConnectorPolicyAction]:
        """Return connector policy actions without enabling runtime execution."""

        actions = [_preview_action(key) for key in PREVIEW_ACTION_KEYS]
        if include_denied:
            actions.extend(_denied_action(key) for key in DENIED_ACTION_KEYS)
        emit_telemetry(
            self._telemetry_service,
            event_type="connector_policy_catalog_read",
            node_type="connector_policy_catalog",
            node_id="connector-policy-catalog-local",
            intensity=0.45,
            trace_id="connector-policy-catalog-local",
            payload={"action_count": len(actions), "runtime_allowed": False},
        )
        return actions

    def get(self, action_key: str) -> ConnectorPolicyAction | None:
        """Return one action from the catalog."""

        for action in self.list_actions(include_denied=True):
            if action.action_key == action_key:
                return action
        return None


def _preview_action(action_key: str) -> ConnectorPolicyAction:
    category = action_key.split(".", 1)[0]
    risk_level: ConnectorPolicyRiskLevel = (
        "medium" if action_key.endswith(("simulate", "replay", "dry_run")) else "low"
    )
    return ConnectorPolicyAction(
        action_key=action_key,
        title=_ACTION_LABELS.get(action_key, action_key.replace(".", " ").title()),
        description="Read-only or dry-run connector policy action; no runtime path is granted.",
        category=category,
        risk_level=risk_level,
        allowed_in_dry_run=True,
        allowed_in_runtime=False,
        requires_operator_review=action_key.endswith(("simulate", "replay", "dry_run")),
        requires_production_auth=False,
        requires_connector_runtime=False,
        requires_credentials=False,
        requires_external_call=False,
        requires_audit=True,
        requires_provenance=True,
        blockers=[
            "connector_runtime_disabled",
            "external_calls_disabled",
            "credentials_tokens_disabled",
            "activation_disabled",
        ],
        metadata={"preview_only": True, "runtime_allowed": False},
    )


def _denied_action(action_key: str) -> ConnectorPolicyAction:
    return ConnectorPolicyAction(
        action_key=action_key,
        title=action_key.replace(".", " ").title(),
        description="Explicit denied future connector action marker; no runtime path exists.",
        category="future_denied_connector_action",
        risk_level="critical",
        allowed_in_dry_run=False,
        allowed_in_runtime=False,
        requires_operator_review=True,
        requires_production_auth=False,
        requires_connector_runtime=False,
        requires_credentials=False,
        requires_external_call=False,
        requires_audit=True,
        requires_provenance=True,
        blockers=[
            "not_implemented",
            "connector_runtime_disabled",
            "external_calls_disabled",
            "credentials_tokens_disabled",
            "activation_disabled",
        ],
        metadata={"denied_future_action": True, "runtime_allowed": False},
    )


__all__ = [
    "DENIED_ACTION_KEYS",
    "PREVIEW_ACTION_KEYS",
    "ConnectorPolicyCatalogService",
]
