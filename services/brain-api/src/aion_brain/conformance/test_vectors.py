"""Capability test vector service."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from aion_brain.api_support.errors import AIONNotFoundException
from aion_brain.config import Settings, get_settings
from aion_brain.conformance.policy import authorize_conformance_action
from aion_brain.conformance.redaction import redact_conformance_payload
from aion_brain.conformance.repository import ConformanceRepository
from aion_brain.conformance.telemetry import emit_conformance_telemetry
from aion_brain.contracts.conformance import (
    CapabilityTestVector,
    CapabilityTestVectorCreateRequest,
)
from aion_brain.module_bindings.repository import ModuleBindingRepository


class CapabilityTestVectorService:
    """Create metadata-only test vectors."""

    def __init__(
        self,
        repository: ConformanceRepository,
        policy_adapter: object,
        *,
        module_binding_repository: ModuleBindingRepository | None = None,
        telemetry_service: object | None = None,
        settings: Settings | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._module_binding_repository = module_binding_repository
        self._telemetry_service = telemetry_service
        self._settings = settings or get_settings()

    def create_vector(self, request: CapabilityTestVectorCreateRequest) -> CapabilityTestVector:
        if not self._settings.capability_test_vectors_enabled:
            raise RuntimeError("capability_test_vectors_disabled")
        authorize_conformance_action(
            self._policy_adapter,
            "conformance.test_vector.create",
            request.owner_scope,
            actor_id=request.created_by,
            resource_type="capability_test_vector",
            risk_level="medium",
            context={"metadata_only": True},
        )
        now = datetime.now(UTC)
        vector = CapabilityTestVector(
            test_vector_id=request.test_vector_id or f"test-vector-{uuid4().hex}",
            trace_id=request.trace_id,
            module_slot_id=request.module_slot_id,
            capability_binding_id=request.capability_binding_id,
            extension_package_id=request.extension_package_id,
            name=request.name,
            description=request.description,
            status="active",
            vector_type=request.vector_type,
            input_payload=redact_conformance_payload(request.input_payload),
            expected_output_shape=redact_conformance_payload(request.expected_output_shape),
            expected_constraints=request.expected_constraints,
            owner_scope=request.owner_scope,
            metadata=redact_conformance_payload(
                {**request.metadata, "metadata_only": True, "capability_invoked": False}
            ),
            created_by=request.created_by,
            created_at=now,
            updated_at=now,
        )
        saved = self._repository.save_vector(vector)
        emit_conformance_telemetry(
            self._telemetry_service,
            event_type="capability_test_vector_created",
            node_type="test_vector",
            node_id=saved.test_vector_id,
            scope=saved.owner_scope,
            intensity=0.4,
            payload={"vector_type": saved.vector_type},
        )
        return saved

    def get_vector(self, test_vector_id: str, scope: list[str]) -> CapabilityTestVector | None:
        authorize_conformance_action(
            self._policy_adapter,
            "conformance.test_vector.read",
            scope,
            resource_type="capability_test_vector",
            resource_id=test_vector_id,
        )
        return self._repository.get_vector(test_vector_id)

    def require_vector(self, test_vector_id: str, scope: list[str]) -> CapabilityTestVector:
        vector = self.get_vector(test_vector_id, scope)
        if vector is None:
            raise AIONNotFoundException("test_vector_not_found")
        return vector

    def list_vectors(
        self,
        scope: list[str],
        *,
        module_slot_id: str | None = None,
        capability_binding_id: str | None = None,
        extension_package_id: str | None = None,
        status: str | None = None,
        vector_type: str | None = None,
        limit: int = 100,
    ) -> list[CapabilityTestVector]:
        authorize_conformance_action(
            self._policy_adapter,
            "conformance.test_vector.read",
            scope,
            resource_type="capability_test_vector",
        )
        return self._repository.list_vectors(
            module_slot_id=module_slot_id,
            capability_binding_id=capability_binding_id,
            extension_package_id=extension_package_id,
            status=status,
            vector_type=vector_type,
            limit=limit,
        )

    def disable_vector(
        self,
        test_vector_id: str,
        scope: list[str],
        actor_id: str | None,
        reason: str,
    ) -> CapabilityTestVector:
        authorize_conformance_action(
            self._policy_adapter,
            "conformance.test_vector.update",
            scope,
            actor_id=actor_id,
            resource_type="capability_test_vector",
            resource_id=test_vector_id,
            risk_level="medium",
        )
        vector = self.require_vector(test_vector_id, scope)
        return self._repository.save_vector(
            vector.model_copy(
                update={
                    "status": "disabled",
                    "disabled_at": datetime.now(UTC),
                    "metadata": {**vector.metadata, "disabled_reason": reason},
                }
            )
        )

    def generate_schema_vectors_for_binding(
        self,
        capability_binding_id: str,
        scope: list[str],
        created_by: str | None = None,
    ) -> list[CapabilityTestVector]:
        """Generate schema vectors without invoking the capability."""

        if self._module_binding_repository is None:
            raise AIONNotFoundException("module_binding_repository_unavailable")
        binding = self._module_binding_repository.get_binding(capability_binding_id)
        if binding is None:
            raise AIONNotFoundException("capability_binding_not_found")
        vector = self.create_vector(
            CapabilityTestVectorCreateRequest(
                trace_id=binding.trace_id,
                module_slot_id=binding.module_slot_id,
                capability_binding_id=binding.capability_binding_id,
                extension_package_id=binding.extension_package_id,
                name=f"Schema vector for {binding.capability_key}",
                description="Generated metadata-only schema vector.",
                vector_type="schema_only",
                input_payload=_sample_payload(binding.input_schema),
                expected_output_shape=binding.output_schema or {"type": "object"},
                expected_constraints=["metadata_only", "no_execution"],
                owner_scope=scope,
                metadata={"generated": True, "capability_invoked": False},
                created_by=created_by,
            )
        )
        return [vector]


def _sample_payload(schema: dict[str, Any]) -> dict[str, Any]:
    required = schema.get("required")
    if isinstance(required, list):
        return {str(key): "sample" for key in required}
    return {}


__all__ = ["CapabilityTestVectorService"]
