"""Module mock schema adapter tests."""

from __future__ import annotations

from aion_brain.module_mock_runtime.schema_adapter import ModuleMockSchemaAdapter
from tests.module_binding_helpers import binding_request


def test_schema_adapter_validates_required_input_and_synthetic_output_shape() -> None:
    binding = binding_request(
        "slot-1",
        capability_binding_id="binding-1",
        input_schema={"type": "object", "required": ["query"]},
    )
    adapter = ModuleMockSchemaAdapter()

    assert adapter.validate_input({"query": "test"}, binding)["valid"] is True
    missing = adapter.validate_input({}, binding)
    assert missing["valid"] is False
    assert missing["errors"] == ["missing_required_input:query"]
    invalid_output = adapter.validate_output_shape({"synthetic": False}, binding)
    assert invalid_output["valid"] is False
