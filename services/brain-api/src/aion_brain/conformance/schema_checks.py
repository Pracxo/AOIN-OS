"""Deterministic schema conformance checks."""

from __future__ import annotations

from typing import Any

from aion_brain.contracts.capability_bindings import CapabilityBinding
from aion_brain.contracts.conformance import CapabilityTestVector
from aion_brain.contracts.model_outputs import reject_secret_like_payload

_FORBIDDEN_FIELDS = {
    "chain_of_thought",
    "code",
    "command",
    "exec",
    "execute",
    "hidden_reasoning",
    "raw_prompt",
    "script",
    "shell",
    "subprocess",
}


class SchemaConformanceChecker:
    """Validate schema-like metadata without executing code."""

    def validate_input_schema(self, binding: CapabilityBinding) -> dict[str, Any]:
        return self._validate_schema(binding.input_schema, "input_schema")

    def validate_output_schema(self, binding: CapabilityBinding) -> dict[str, Any]:
        return self._validate_schema(binding.output_schema, "output_schema")

    def validate_test_vector(
        self,
        vector: CapabilityTestVector,
        binding: CapabilityBinding | None,
    ) -> dict[str, Any]:
        findings: list[dict[str, Any]] = []
        if _contains_forbidden(vector.input_payload):
            findings.append(
                _finding("unsafe_metadata", "Test vector input contains unsafe fields.")
            )
        if binding is not None:
            required = binding.input_schema.get("required")
            if isinstance(required, list):
                missing = [str(key) for key in required if str(key) not in vector.input_payload]
                if missing:
                    findings.append(
                        _finding(
                            "invalid_test_vector",
                            "Test vector does not include required input keys.",
                            metadata={"missing": missing},
                        )
                    )
        return _result("test_vector", findings)

    def _validate_schema(self, schema: dict[str, Any], name: str) -> dict[str, Any]:
        findings: list[dict[str, Any]] = []
        if not isinstance(schema, dict):
            findings.append(_finding(f"invalid_{name}", "Schema must be a JSON object."))
        if schema.get("type") not in (None, "object"):
            findings.append(_finding(f"invalid_{name}", "Schema type must be object-like."))
        required = schema.get("required")
        if required is not None and not isinstance(required, list):
            findings.append(_finding(f"invalid_{name}", "Schema required field must be a list."))
        try:
            reject_secret_like_payload(schema)
        except ValueError as exc:
            findings.append(_finding("unsafe_metadata", str(exc), severity="critical"))
        if _contains_forbidden(schema):
            findings.append(
                _finding("unsafe_metadata", "Schema contains executable or protected fields.")
            )
        return _result(name, findings)


def _result(name: str, findings: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "check": name,
        "passed": not findings,
        "findings": findings,
        "blockers": [item for item in findings if item["severity"] in {"high", "critical"}],
        "warnings": [item for item in findings if item["severity"] in {"low", "medium"}],
    }


def _finding(
    finding_type: str,
    description: str,
    *,
    severity: str = "high",
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "finding_type": finding_type,
        "severity": severity,
        "description": description,
        "metadata": metadata or {},
    }


def _contains_forbidden(value: object) -> bool:
    if isinstance(value, dict):
        for key, nested in value.items():
            lowered = str(key).lower().replace("-", "_")
            if lowered in _FORBIDDEN_FIELDS:
                return True
            if _contains_forbidden(nested):
                return True
    if isinstance(value, list):
        return any(_contains_forbidden(item) for item in value)
    return False


__all__ = ["SchemaConformanceChecker"]
