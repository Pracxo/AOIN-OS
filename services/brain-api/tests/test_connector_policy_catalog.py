from __future__ import annotations

from aion_brain.connector_policy.catalog import (
    DENIED_ACTION_KEYS,
    PREVIEW_ACTION_KEYS,
    ConnectorPolicyCatalogService,
)


def test_connector_policy_catalog_contains_preview_and_denied_actions() -> None:
    actions = ConnectorPolicyCatalogService().list_actions()
    keys = {action.action_key for action in actions}

    assert set(PREVIEW_ACTION_KEYS) <= keys
    assert set(DENIED_ACTION_KEYS) <= keys
    assert "connector_policy.catalog.read" in keys
    assert "connector_policy.dry_run" in keys
    assert all(action.allowed_in_runtime is False for action in actions)
    assert all(action.requires_external_call is False for action in actions)

