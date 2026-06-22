"""Module binding visual and resource vocabulary tests."""

from typing import get_args

from aion_brain.contracts.resource_registry import ResourceType
from aion_brain.contracts.telemetry import VisualNodeType, VisualTelemetryEventType
from aion_brain.contracts.visual import BrainVisualNodeType


def test_module_binding_visual_telemetry_vocabulary_exists() -> None:
    event_types = set(get_args(VisualTelemetryEventType))
    node_types = set(get_args(VisualNodeType))
    brain_node_types = set(get_args(BrainVisualNodeType))

    assert "module_slot_created" in event_types
    assert "capability_binding_created" in event_types
    assert "binding_validation_completed" in event_types
    assert "module_slot" in node_types
    assert "capability_binding" in node_types
    assert "module_mount_plan" in brain_node_types
    assert "route_binding_preview" in brain_node_types


def test_module_binding_resource_types_exist() -> None:
    resource_types = set(get_args(ResourceType))

    assert "module_slot" in resource_types
    assert "capability_binding" in resource_types
    assert "module_mount_plan" in resource_types
    assert "route_binding_preview" in resource_types
    assert "binding_validation" in resource_types
