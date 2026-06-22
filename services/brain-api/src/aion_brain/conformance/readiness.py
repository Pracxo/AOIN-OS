"""Extension readiness assessment service."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, cast
from uuid import uuid4

from aion_brain.api_support.errors import AIONNotFoundException
from aion_brain.config import Settings, get_settings
from aion_brain.conformance.policy import authorize_conformance_action
from aion_brain.conformance.repository import ConformanceRepository
from aion_brain.conformance.telemetry import emit_conformance_telemetry
from aion_brain.contracts.readiness import ReadinessAssessment, ReadinessAssessmentRequest


class ReadinessAssessmentService:
    """Assess future activation readiness without activating anything."""

    def __init__(
        self,
        repository: ConformanceRepository,
        policy_adapter: object,
        *,
        telemetry_service: object | None = None,
        settings: Settings | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._telemetry_service = telemetry_service
        self._settings = settings or get_settings()

    def assess(self, request: ReadinessAssessmentRequest) -> ReadinessAssessment:
        if not self._settings.extension_readiness_gate_enabled:
            raise RuntimeError("extension_readiness_gate_disabled")
        authorize_conformance_action(
            self._policy_adapter,
            "conformance.readiness.assess",
            request.owner_scope,
            actor_id=request.actor_id,
            workspace_id=request.workspace_id,
            trace_id=request.trace_id,
            resource_type="readiness_assessment",
            risk_level="medium",
            context={"activation_ready": False, "metadata_only": True},
        )
        runs = self._repository.list_runs(
            module_slot_id=request.module_slot_id,
            capability_binding_id=request.capability_binding_id,
            extension_package_id=request.extension_package_id,
            limit=50,
        )
        missing_required_conformance = request.require_passing_conformance and not runs
        blocker_refs = [
            run.conformance_run_id
            for run in runs
            if run.status in {"failed", "blocked"} or bool(run.blockers)
        ]
        if missing_required_conformance:
            blocker_refs.append("missing_conformance_run")
        warning_refs = [
            run.conformance_run_id for run in runs if run.status in {"warning", "dry_run"}
        ]
        actual_score = max((run.score for run in runs), default=0.0)
        minimum_score = 0.8
        recommendations = _recommendations(request, bool(runs), blocker_refs)
        readiness_level = _level(request, runs, blocker_refs, actual_score, minimum_score)
        status = "blocked" if blocker_refs and request.require_no_blockers else "ready"
        if readiness_level == "not_ready":
            status = "failed"
        elif warning_refs and status == "ready":
            status = "warning"
        assessment = ReadinessAssessment(
            readiness_assessment_id=(
                request.readiness_assessment_id or f"readiness-assessment-{uuid4().hex}"
            ),
            trace_id=request.trace_id,
            actor_id=request.actor_id,
            workspace_id=request.workspace_id,
            extension_package_id=request.extension_package_id,
            module_slot_id=request.module_slot_id,
            capability_binding_id=request.capability_binding_id,
            status=cast(Any, status),
            readiness_level=cast(Any, readiness_level),
            activation_ready=False,
            minimum_score=minimum_score,
            actual_score=actual_score,
            conformance_run_ids=[run.conformance_run_id for run in runs],
            compatibility_run_ids=[],
            validation_run_ids=[],
            blocker_refs=blocker_refs,
            warning_refs=warning_refs,
            recommendations=recommendations,
            owner_scope=request.owner_scope,
            metadata={**request.metadata, "metadata_only": True, "activation_performed": False},
            created_by=request.created_by,
            created_at=datetime.now(UTC),
            completed_at=datetime.now(UTC),
        )
        saved = self._repository.save_readiness(assessment)
        emit_conformance_telemetry(
            self._telemetry_service,
            event_type="readiness_assessment_created",
            node_type="readiness_assessment",
            node_id=saved.readiness_assessment_id,
            scope=saved.owner_scope,
            intensity=saved.actual_score,
            payload={"status": saved.status, "readiness_level": saved.readiness_level},
        )
        return saved

    def get_assessment(
        self,
        readiness_assessment_id: str,
        scope: list[str],
    ) -> ReadinessAssessment | None:
        authorize_conformance_action(
            self._policy_adapter,
            "conformance.readiness.read",
            scope,
            resource_type="readiness_assessment",
            resource_id=readiness_assessment_id,
        )
        return self._repository.get_readiness(readiness_assessment_id)

    def require_assessment(
        self,
        readiness_assessment_id: str,
        scope: list[str],
    ) -> ReadinessAssessment:
        assessment = self.get_assessment(readiness_assessment_id, scope)
        if assessment is None:
            raise AIONNotFoundException("readiness_assessment_not_found")
        return assessment

    def list_assessments(
        self,
        scope: list[str],
        *,
        status: str | None = None,
        readiness_level: str | None = None,
        limit: int = 100,
    ) -> list[ReadinessAssessment]:
        authorize_conformance_action(
            self._policy_adapter,
            "conformance.readiness.read",
            scope,
            resource_type="readiness_assessment",
        )
        return self._repository.list_readiness(
            status=status,
            readiness_level=readiness_level,
            limit=limit,
        )


def _level(
    request: ReadinessAssessmentRequest,
    runs: list[Any],
    blocker_refs: list[str],
    actual_score: float,
    minimum_score: float,
) -> str:
    if blocker_refs:
        return "blocked"
    if runs and actual_score >= minimum_score:
        return "conformant"
    if request.extension_package_id or request.module_slot_id or request.capability_binding_id:
        return "metadata_only"
    return "not_ready"


def _recommendations(
    request: ReadinessAssessmentRequest,
    has_runs: bool,
    blocker_refs: list[str],
) -> list[str]:
    recommendations = ["keep_activation_disabled"]
    if not has_runs and request.require_passing_conformance:
        recommendations.append("run_conformance")
    if blocker_refs:
        recommendations.append("resolve_binding_conflicts")
    if request.require_approved_review:
        recommendations.append("review_extension")
    return recommendations


__all__ = ["ReadinessAssessmentService"]
