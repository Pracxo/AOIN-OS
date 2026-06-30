from __future__ import annotations

from aion_brain.connector_sandbox.capabilities import (
    DENIED_CAPABILITY_KEYS,
    PREVIEW_CAPABILITY_KEYS,
    ConnectorSandboxCapabilityRuleService,
)


def test_connector_sandbox_capability_rules_include_preview_and_denials() -> None:
    rules = ConnectorSandboxCapabilityRuleService().list_rules()
    keys = {rule.rule_key for rule in rules}

    assert set(PREVIEW_CAPABILITY_KEYS) <= keys
    assert set(DENIED_CAPABILITY_KEYS) <= keys
    assert "connector.sandbox.readiness.preview" in keys
    assert all(rule.runtime_allowed is False for rule in rules)
    assert all(
        rule.allowed is False
        for rule in rules
        if rule.rule_key in set(DENIED_CAPABILITY_KEYS)
    )
