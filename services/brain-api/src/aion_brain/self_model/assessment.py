"""Self-assessment service."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any, cast
from uuid import uuid4

from aion_brain.contracts.confidence import SelfAssessmentRequest, SelfAssessmentRun
from aion_brain.outcomes._shared import audit_optional, authorize, emit_telemetry
from aion_brain.self_model.repository import SelfModelRepository


class SelfAssessmentService:
    """Run deterministic read-only self-assessments."""

    def __init__(
        self,
        repository: SelfModelRepository,
        policy_adapter: object,
        *,
        profile_service: Any,
        capability_awareness_service: Any,
        limitation_service: Any,
        settings: object | None = None,
        telemetry_service: object | None = None,
        audit_sink: object | None = None,
        provenance_service: object | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._profile_service = profile_service
        self._capability_awareness_service = capability_awareness_service
        self._limitation_service = limitation_service
        self._settings = settings
        self._telemetry_service = telemetry_service
        self._audit_sink = audit_sink
        self._provenance_service = provenance_service

    def run(self, request: SelfAssessmentRequest) -> SelfAssessmentRun:
        authorize(
            self._policy_adapter,
            action_type="self_model.assessment.run",
            resource_type="self_assessment",
            resource_id=request.self_assessment_id,
            scope=request.owner_scope,
            trace_id=request.trace_id,
            risk_level="low",
            context={"assessment_type": request.assessment_type, "dry_run": request.dry_run},
        )
        emit_telemetry(
            self._telemetry_service,
            event_type="self_assessment_started",
            node_type="self_assessment",
            node_id=request.self_assessment_id or "pending",
            intensity=0.4,
            trace_id=request.trace_id,
            payload={"owner_scope": request.owner_scope},
        )
        capabilities = (
            self._capability_awareness_service.refresh(request.owner_scope, dry_run=True)
            if request.include_capabilities
            else []
        )
        limitations = (
            self._limitation_service.list_limitations(request.owner_scope, status="active")
            if request.include_limitations
            else []
        )
        profile = self._profile_service.get_active_profile(request.owner_scope)
        findings = _findings(profile, capabilities, limitations, self._settings)
        status = _assessment_status(findings)
        now = datetime.now(UTC)
        run = SelfAssessmentRun(
            self_assessment_id=request.self_assessment_id or f"self-assessment-{uuid4().hex}",
            trace_id=request.trace_id,
            status=cast(Any, status),
            owner_scope=request.owner_scope,
            assessment_type=request.assessment_type,
            capability_count=len(capabilities),
            active_capability_count=sum(1 for item in capabilities if item.status == "active"),
            disabled_capability_count=sum(1 for item in capabilities if item.status == "disabled"),
            unavailable_capability_count=sum(
                1 for item in capabilities if "unavailable" in item.availability
            ),
            limitation_count=len(limitations),
            critical_limitation_count=sum(1 for item in limitations if item.severity == "critical"),
            findings=findings,
            recommendations=_recommendations(findings),
            report={
                "dry_run": request.dry_run,
                "external_model_calls_enabled": bool(
                    getattr(self._settings, "model_gateway_enabled", False)
                ),
                "descriptive_self_model": True,
            },
            created_by=request.created_by,
            created_at=now,
            completed_at=now,
        )
        stored = self._repository.save_assessment_run(run)
        audit_optional(
            self._audit_sink,
            "self_assessment_completed",
            {"self_assessment_id": stored.self_assessment_id, "status": stored.status},
        )
        emit_telemetry(
            self._telemetry_service,
            event_type="self_assessment_completed",
            node_type="self_assessment",
            node_id=stored.self_assessment_id,
            intensity=1.0 if stored.status == "failed" else 0.8,
            trace_id=stored.trace_id,
            payload={"owner_scope": stored.owner_scope, "status": stored.status},
        )
        _link_assessment(self._provenance_service, stored, capabilities)
        return stored

    def get(self, self_assessment_id: str) -> SelfAssessmentRun | None:
        return self._repository.get_assessment_run(self_assessment_id)

    def list(self, scope: list[str], limit: int = 100) -> list[SelfAssessmentRun]:
        authorize(
            self._policy_adapter,
            action_type="self_model.assessment.read",
            resource_type="self_assessment",
            resource_id=None,
            scope=scope,
            risk_level="low",
        )
        return self._repository.list_assessment_runs(scope, limit=limit)

    def status(self, scope: Sequence[str] | None = None) -> dict[str, Any]:
        runs = self.list([*scope] if scope is not None else ["workspace:main"], limit=1)
        if not runs:
            return {"status": "warning", "latest_self_assessment_id": None}
        return {"status": runs[0].status, "latest_self_assessment_id": runs[0].self_assessment_id}


def _findings(
    profile: object,
    capabilities: list[object],
    limitations: list[object],
    settings: object | None,
) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    text = f"{getattr(profile, 'description', '')} {getattr(profile, 'metadata', {})}".lower()
    if any(marker in text for marker in ("sentient", "conscious", "self-aware")):
        findings.append({"code": "unsafe_self_claim", "severity": "critical"})
    if any(marker in text for marker in ("production ready", "production-ready")):
        findings.append({"code": "production_readiness_claim", "severity": "critical"})
    if any(
        getattr(item, "severity", None) == "critical"
        and not bool(getattr(item, "disclosure_required", False))
        for item in limitations
    ):
        findings.append({"code": "critical_limitation_not_disclosed", "severity": "critical"})
    if any(getattr(item, "availability", None) == "optional_unavailable" for item in capabilities):
        findings.append({"code": "optional_adapter_unavailable", "severity": "medium"})
    if bool(getattr(settings, "model_gateway_enabled", False)):
        findings.append({"code": "external_model_calls_enabled", "severity": "medium"})
    return findings


def _assessment_status(findings: list[dict[str, Any]]) -> str:
    if any(item.get("severity") == "critical" for item in findings):
        return "failed"
    if findings:
        return "warning"
    return "passed"


def _recommendations(findings: list[dict[str, Any]]) -> list[str]:
    if not findings:
        return ["Keep descriptive self-model records current."]
    return [f"review_{item['code']}" for item in findings]


def _link_assessment(
    provenance_service: object | None,
    run: SelfAssessmentRun,
    capabilities: list[object],
) -> None:
    link = getattr(provenance_service, "create_link", None)
    if not callable(link):
        return
    for capability in capabilities[:25]:
        try:
            link(
                source_id=run.self_assessment_id,
                target_id=getattr(capability, "awareness_id", None),
                relation_type="assessed_capability_awareness",
            )
        except Exception:
            return
