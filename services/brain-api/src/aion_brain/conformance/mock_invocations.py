"""Schema-only mock invocation simulator."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, cast
from uuid import uuid4

from aion_brain.api_support.errors import AIONNotFoundException
from aion_brain.config import Settings, get_settings
from aion_brain.conformance.hash import hash_mock_input
from aion_brain.conformance.redaction import redact_conformance_payload
from aion_brain.conformance.repository import ConformanceRepository
from aion_brain.conformance.schema_checks import SchemaConformanceChecker
from aion_brain.conformance.telemetry import emit_conformance_telemetry
from aion_brain.contracts.capability_bindings import CapabilityBinding
from aion_brain.contracts.conformance import CapabilityTestVector, MockInvocationRecord
from aion_brain.module_bindings.repository import ModuleBindingRepository


class MockInvocationSimulator:
    """Build deterministic mock records without invoking capabilities."""

    def __init__(
        self,
        repository: ConformanceRepository,
        *,
        schema_checker: SchemaConformanceChecker,
        module_binding_repository: ModuleBindingRepository | None = None,
        telemetry_service: object | None = None,
        settings: Settings | None = None,
    ) -> None:
        self._repository = repository
        self._schema_checker = schema_checker
        self._module_binding_repository = module_binding_repository
        self._telemetry_service = telemetry_service
        self._settings = settings or get_settings()

    def simulate(
        self,
        vector: CapabilityTestVector,
        binding: CapabilityBinding | None,
        created_by: str | None = None,
    ) -> MockInvocationRecord:
        if not self._settings.mock_invocation_simulator_enabled:
            raise RuntimeError("mock_invocation_simulator_disabled")
        vector_result = self._schema_checker.validate_test_vector(vector, binding)
        input_result = (
            self._schema_checker.validate_input_schema(binding)
            if binding is not None
            else {"passed": True, "findings": []}
        )
        output_result = (
            self._schema_checker.validate_output_schema(binding)
            if binding is not None
            else {"passed": True, "findings": []}
        )
        findings: list[dict[str, Any]] = []
        for result in (vector_result, input_result, output_result):
            result_findings = result.get("findings", [])
            if isinstance(result_findings, list):
                findings.extend(cast(list[dict[str, Any]], result_findings))
        schema_valid = not findings
        policy_valid = bool(not binding or binding.required_policy_actions)
        sandbox_valid = bool(
            not binding or not binding.requires_sandbox or binding.sandbox_profile_id
        )
        if not policy_valid:
            findings.append(_finding("missing_policy_action", "Policy action metadata is missing."))
        if not sandbox_valid:
            findings.append(_finding("missing_sandbox", "Sandbox metadata is missing."))
        status = _status(schema_valid, policy_valid, sandbox_valid, findings)
        simulated_output = _simulated_output(vector.expected_output_shape)
        record = MockInvocationRecord(
            mock_invocation_id=f"mock-invocation-{uuid4().hex}",
            trace_id=vector.trace_id,
            module_slot_id=vector.module_slot_id or (binding.module_slot_id if binding else None),
            capability_binding_id=vector.capability_binding_id
            or (binding.capability_binding_id if binding else None),
            extension_package_id=vector.extension_package_id
            or (binding.extension_package_id if binding else None),
            test_vector_id=vector.test_vector_id,
            status=cast(Any, status),
            invocation_type="schema_simulation",
            input_payload_hash=hash_mock_input(vector.input_payload),
            redacted_input_payload=redact_conformance_payload(vector.input_payload),
            simulated_output=simulated_output,
            schema_valid=schema_valid,
            policy_valid=policy_valid,
            sandbox_valid=sandbox_valid,
            findings=findings,
            metadata={
                "mock_only": True,
                "capability_executed": False,
                "extension_code_loaded": False,
            },
            created_by=created_by,
            created_at=datetime.now(UTC),
        )
        emit_conformance_telemetry(
            self._telemetry_service,
            event_type="mock_invocation_simulated",
            node_type="mock_invocation",
            node_id=record.mock_invocation_id,
            scope=vector.owner_scope,
            intensity=0.7 if record.status == "passed" else 1.0,
            payload={"status": record.status},
        )
        return record

    def simulate_for_binding(
        self,
        capability_binding_id: str,
        vector_ids: list[str],
        scope: list[str],
        created_by: str | None = None,
    ) -> list[MockInvocationRecord]:
        if self._module_binding_repository is None:
            raise AIONNotFoundException("module_binding_repository_unavailable")
        binding = self._module_binding_repository.get_binding(capability_binding_id)
        if binding is None:
            raise AIONNotFoundException("capability_binding_not_found")
        vectors = (
            [self._repository.get_vector(vector_id) for vector_id in vector_ids]
            if vector_ids
            else self._repository.list_vectors(
                capability_binding_id=capability_binding_id, limit=100
            )
        )
        return [
            self.simulate(vector, binding, created_by)
            for vector in vectors
            if vector is not None and vector.owner_scope == scope
        ]


def _simulated_output(shape: dict[str, Any]) -> dict[str, Any]:
    properties = shape.get("properties")
    if isinstance(properties, dict):
        return {str(key): _placeholder(value) for key, value in properties.items()}
    return {"mock": True, "metadata_only": True}


def _placeholder(value: object) -> object:
    if not isinstance(value, dict):
        return None
    kind = value.get("type")
    if kind == "number" or kind == "integer":
        return 0
    if kind == "boolean":
        return False
    if kind == "array":
        return []
    if kind == "object":
        return {}
    return "mock"


def _finding(finding_type: str, description: str) -> dict[str, Any]:
    return {"finding_type": finding_type, "severity": "high", "description": description}


def _status(
    schema_valid: bool,
    policy_valid: bool,
    sandbox_valid: bool,
    findings: list[dict[str, Any]],
) -> str:
    if any(item.get("severity") == "critical" for item in findings):
        return "blocked"
    if not schema_valid:
        return "failed"
    if not policy_valid or not sandbox_valid:
        return "blocked"
    return "passed"


__all__ = ["MockInvocationSimulator"]
