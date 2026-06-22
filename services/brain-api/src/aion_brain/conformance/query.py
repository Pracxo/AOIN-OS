"""Query service for capability conformance records."""

from __future__ import annotations

from aion_brain.conformance.policy import authorize_conformance_action
from aion_brain.conformance.repository import ConformanceRepository
from aion_brain.contracts.conformance import ConformanceQuery, ConformanceQueryResult


class ConformanceQueryService:
    """Query metadata-only conformance and readiness records."""

    def __init__(self, repository: ConformanceRepository, policy_adapter: object) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter

    def query(self, request: ConformanceQuery) -> ConformanceQueryResult:
        """Return conformance records through AION-owned contracts."""

        authorize_conformance_action(
            self._policy_adapter,
            "conformance.query",
            request.scope,
            resource_type="conformance_registry",
            risk_level="low",
            context=request.model_dump(mode="json"),
        )
        profiles = self._repository.list_profiles(
            status=request.status,
            profile_type=request.profile_type,
            include_disabled=request.include_disabled,
            limit=request.limit,
        )
        vectors = self._repository.list_vectors(
            module_slot_id=request.module_slot_id,
            capability_binding_id=request.capability_binding_id,
            extension_package_id=request.extension_package_id,
            include_disabled=request.include_disabled,
            limit=request.limit,
        )
        runs = self._repository.list_runs(
            status=request.status,
            module_slot_id=request.module_slot_id,
            capability_binding_id=request.capability_binding_id,
            extension_package_id=request.extension_package_id,
            limit=request.limit,
        )
        findings = self._repository.list_findings(
            status=request.status,
            module_slot_id=request.module_slot_id,
            capability_binding_id=request.capability_binding_id,
            extension_package_id=request.extension_package_id,
            limit=request.limit,
        )
        readiness = self._repository.list_readiness(
            status=request.status,
            module_slot_id=request.module_slot_id,
            capability_binding_id=request.capability_binding_id,
            extension_package_id=request.extension_package_id,
            limit=request.limit,
        )
        return ConformanceQueryResult(
            profiles=profiles,
            test_vectors=vectors,
            runs=runs,
            findings=findings,
            readiness_assessments=readiness,
            total_count=(len(profiles) + len(vectors) + len(runs) + len(findings) + len(readiness)),
            constraints=[
                "metadata_only",
                "no_code_loading",
                "no_package_install",
                "no_activation",
                "no_external_calls",
            ],
            metadata={"source_records_mutated": False},
        )


__all__ = ["ConformanceQueryService"]
