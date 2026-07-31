"""Restricted schema validation for transient capability payloads."""

from aion_brain.contracts.sandboxed_capability_runtime import (
    CapabilityInputSchema,
    CapabilityOutputSchema,
    ReferenceConnectorRequestSchema,
    ReferenceConnectorResponseSchema,
    validate_json_against_schema,
)

__all__ = [
    "CapabilityInputSchema",
    "CapabilityOutputSchema",
    "ReferenceConnectorRequestSchema",
    "ReferenceConnectorResponseSchema",
    "validate_json_against_schema",
]
