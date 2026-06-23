from __future__ import annotations

from aion_brain.operator_console.action_boundaries import (
    allowed_action_descriptors,
    forbidden_action_descriptors,
)


def test_forbidden_actions_include_activation_and_execution_boundaries() -> None:
    forbidden = {descriptor.action_key: descriptor for descriptor in forbidden_action_descriptors()}

    assert forbidden["activate_module"].forbidden is True
    assert forbidden["execute_tool"].forbidden is True
    assert forbidden["activate_module"].reason
    assert all(descriptor.action_type == "forbidden" for descriptor in forbidden.values())


def test_allowed_actions_are_descriptors_only() -> None:
    actions = allowed_action_descriptors()

    assert {action.forbidden for action in actions} == {False}
    assert all(action.metadata["descriptor_only"] is True for action in actions)
    assert not any(action.action_key.startswith("activate") for action in actions)
