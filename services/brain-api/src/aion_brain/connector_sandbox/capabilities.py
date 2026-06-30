"""Connector sandbox capability rules."""

from __future__ import annotations

from aion_brain.contracts.connector_sandbox import ConnectorSandboxCapabilityRule
from aion_brain.dialogue._shared import emit_telemetry

PREVIEW_CAPABILITY_KEYS = ("connector.sandbox.readiness.preview",)

DENIED_CAPABILITY_KEYS = (
    "connector.sandbox.filesystem.read",
    "connector.sandbox.filesystem.write",
    "connector.sandbox.network.egress",
    "connector.sandbox.network.ingress",
    "connector.sandbox.credentials.read",
    "connector.sandbox.tokens.read",
    "connector.sandbox.process.spawn",
    "connector.sandbox.dynamic_import",
    "connector.sandbox.package_install",
    "connector.sandbox.runtime.execute",
    "connector.sandbox.activate",
)

_CAPABILITY_LABELS = {
    "connector.sandbox.readiness.preview": "Connector Sandbox Readiness Preview",
    "connector.sandbox.filesystem.read": "Connector Sandbox Filesystem Read",
    "connector.sandbox.filesystem.write": "Connector Sandbox Filesystem Write",
    "connector.sandbox.network.egress": "Connector Sandbox Network Egress",
    "connector.sandbox.network.ingress": "Connector Sandbox Network Ingress",
    "connector.sandbox.credentials.read": "Connector Sandbox Credentials Read",
    "connector.sandbox.tokens.read": "Connector Sandbox Tokens Read",
    "connector.sandbox.process.spawn": "Connector Sandbox Process Spawn",
    "connector.sandbox.dynamic_import": "Connector Sandbox Dynamic Import",
    "connector.sandbox.package_install": "Connector Sandbox Package Install",
    "connector.sandbox.runtime.execute": "Connector Sandbox Runtime Execute",
    "connector.sandbox.activate": "Connector Sandbox Activate",
}


class ConnectorSandboxCapabilityRuleService:
    """Return deterministic connector sandbox capability rules."""

    def __init__(self, *, telemetry_service: object | None = None) -> None:
        self._telemetry_service = telemetry_service

    def list_rules(self, *, include_denied: bool = True) -> list[ConnectorSandboxCapabilityRule]:
        """Return capability rules without enabling restricted sandbox capabilities."""

        rules = [_preview_rule(key) for key in PREVIEW_CAPABILITY_KEYS]
        if include_denied:
            rules.extend(_denied_rule(key) for key in DENIED_CAPABILITY_KEYS)
        emit_telemetry(
            self._telemetry_service,
            event_type="connector_sandbox_capability_rules_read",
            node_type="connector_sandbox_capability_rules",
            node_id="connector-sandbox-capability-rules-local",
            intensity=0.45,
            trace_id="connector-sandbox-capability-rules-local",
            payload={"rule_count": len(rules), "runtime_allowed": False},
        )
        return rules

    def get(self, rule_key: str) -> ConnectorSandboxCapabilityRule | None:
        """Return one capability rule by key."""

        for rule in self.list_rules(include_denied=True):
            if rule.rule_key == rule_key:
                return rule
        return None


def _preview_rule(rule_key: str) -> ConnectorSandboxCapabilityRule:
    return ConnectorSandboxCapabilityRule(
        rule_key=rule_key,
        title=_CAPABILITY_LABELS.get(rule_key, rule_key.replace(".", " ").title()),
        description="Read-only sandbox readiness preview; no sandbox execution is granted.",
        category="readiness",
        allowed=True,
        dry_run_allowed=True,
        runtime_allowed=False,
        requires_review=True,
        requires_policy=True,
        requires_audit=True,
        blockers=[
            {"blocker_key": "real_sandbox_runtime_absent", "bypassable": False},
            {"blocker_key": "runtime_execution_disabled", "bypassable": False},
        ],
        metadata={"preview_only": True, "runtime_allowed": False},
    )


def _denied_rule(rule_key: str) -> ConnectorSandboxCapabilityRule:
    category = rule_key.split(".")[2] if len(rule_key.split(".")) > 2 else "sandbox"
    return ConnectorSandboxCapabilityRule(
        rule_key=rule_key,
        title=_CAPABILITY_LABELS.get(rule_key, rule_key.replace(".", " ").title()),
        description="Denied future sandbox capability; no sandbox runtime path exists.",
        category=category,
        allowed=False,
        dry_run_allowed=False,
        runtime_allowed=False,
        requires_review=True,
        requires_policy=True,
        requires_audit=True,
        blockers=[
            {"blocker_key": "not_implemented", "bypassable": False},
            {"blocker_key": "real_sandbox_runtime_absent", "bypassable": False},
            {"blocker_key": "runtime_execution_disabled", "bypassable": False},
        ],
        metadata={"denied_future_capability": True, "runtime_allowed": False},
    )


__all__ = [
    "DENIED_CAPABILITY_KEYS",
    "PREVIEW_CAPABILITY_KEYS",
    "ConnectorSandboxCapabilityRuleService",
]
