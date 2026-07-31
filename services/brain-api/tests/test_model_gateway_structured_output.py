from __future__ import annotations

import pytest

from aion_brain.contracts.model_gateway import (
    ModelStructuredOutputSchema,
    validate_structured_schema_definition,
)
from tests.model_gateway_aion233_test_support import structured_schema


def test_structured_schema_uses_closed_standard_library_subset() -> None:
    schema = structured_schema()
    assert schema.additional_properties_allowed is False
    assert schema.tool_calling_enabled is False
    assert schema.function_calling_enabled is False
    validate_structured_schema_definition(schema.schema_definition)


def test_schema_smuggling_and_depth_overflow_are_rejected() -> None:
    with pytest.raises(ValueError):
        ModelStructuredOutputSchema(
            schema_id="bad-schema",
            schema_definition={"$ref": "https://example.invalid/schema.json"},
            schema_byte_count=10,
            schema_depth=1,
        )
    with pytest.raises(ValueError):
        ModelStructuredOutputSchema(
            schema_id="deep-schema",
            schema_definition={"type": "object", "additionalProperties": False},
            schema_byte_count=10,
            schema_depth=17,
        )
