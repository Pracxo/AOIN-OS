"""Schema-shape adapter for deterministic module mock runs."""

from __future__ import annotations

from typing import Any

from aion_brain.contracts.capability_bindings import CapabilityBinding
from aion_brain.module_mock_runtime.redaction import redact_module_mock_payload


class ModuleMockSchemaAdapter:
    """Validate JSON-like shapes without executing module code."""

    def validate_input(
        self,
        payload: dict[str, Any],
        binding: CapabilityBinding | None,
    ) -> dict[str, Any]:
        """Return deterministic input-shape validation metadata."""

        errors: list[str] = []
        redacted = redact_module_mock_payload(payload)
        schema = binding.input_schema if binding is not None else {}
        required = list(schema.get("required") or [])
        for key in required:
            if key not in redacted:
                errors.append(f"missing_required_input:{key}")
        if not isinstance(redacted, dict):
            errors.append("input_must_be_object")
        return {
            "valid": not errors,
            "errors": errors,
            "redacted_payload": redacted,
            "schema_ref": binding.capability_binding_id if binding else None,
        }

    def normalize_output_shape(
        self,
        expected_output_shape: dict[str, Any],
        binding: CapabilityBinding | None,
    ) -> dict[str, Any]:
        """Return a safe output shape from request or binding metadata."""

        base = expected_output_shape or (binding.output_schema if binding is not None else {})
        normalized = redact_module_mock_payload(base)
        return normalized if isinstance(normalized, dict) else {"type": "object"}

    def validate_output_shape(
        self,
        output_shape: dict[str, Any],
        binding: CapabilityBinding | None,
    ) -> dict[str, Any]:
        """Validate that output remains synthetic JSON-like metadata."""

        errors: list[str] = []
        if not isinstance(output_shape, dict):
            errors.append("output_shape_must_be_object")
        if output_shape.get("synthetic") is False:
            errors.append("output_must_be_synthetic")
        return {
            "valid": not errors,
            "errors": errors,
            "schema_ref": binding.capability_binding_id if binding else None,
        }


__all__ = ["ModuleMockSchemaAdapter"]
