"""Conformance telemetry and resource vocabulary tests."""

from typing import get_args

from aion_brain.contracts.resource_registry import ResourceType
from aion_brain.contracts.telemetry import VisualNodeType, VisualTelemetryEventType


def test_conformance_visual_telemetry_vocabulary_exists() -> None:
    events = set(get_args(VisualTelemetryEventType))
    nodes = set(get_args(VisualNodeType))

    assert "conformance_run_completed" in events
    assert "readiness_assessment_created" in events
    assert "conformance_profile" in nodes
    assert "readiness_assessment" in nodes


def test_conformance_resource_types_exist() -> None:
    resource_types = set(get_args(ResourceType))

    assert "conformance_profile" in resource_types
    assert "capability_test_vector" in resource_types
    assert "conformance_run" in resource_types
    assert "conformance_finding" in resource_types
    assert "readiness_assessment" in resource_types
