from __future__ import annotations

from types import SimpleNamespace

from aion_brain.contracts.confidence import SelfAssessmentRequest
from aion_brain.self_model.assessment import SelfAssessmentService
from aion_brain.self_model.repository import SelfModelRepository
from tests.self_model_helpers import AllowPolicy, FakeAuditSink, FakeProvenance, bundle, settings


class UnsafeProfileService:
    def get_active_profile(self, scope: list[str]) -> SimpleNamespace:
        return SimpleNamespace(description="AION is production ready.", metadata={})


class EmptyCapabilityService:
    def refresh(self, scope: list[str], dry_run: bool = True) -> list[object]:
        return []


class EmptyLimitationService:
    def list_limitations(self, scope: list[str], status: str | None = None) -> list[object]:
        return []


def test_self_assessment_fails_unsafe_production_readiness_claim() -> None:
    service = SelfAssessmentService(
        SelfModelRepository(),
        AllowPolicy(),
        profile_service=UnsafeProfileService(),
        capability_awareness_service=EmptyCapabilityService(),
        limitation_service=EmptyLimitationService(),
        settings=settings(),
    )

    run = service.run(SelfAssessmentRequest(owner_scope=["workspace:main"]))

    assert run.status == "failed"
    assert any(item["code"] == "production_readiness_claim" for item in run.findings)


def test_self_assessment_warns_on_optional_adapter_unavailable_and_records_audit() -> None:
    services = bundle()

    run = services.assessment.run(SelfAssessmentRequest(owner_scope=["workspace:main"]))

    assert run.status == "warning"
    assert any(item["code"] == "optional_adapter_unavailable" for item in run.findings)
    assert any(event[0] == "self_assessment_completed" for event in services.audit.events)
    assert services.provenance.links


def test_self_assessment_uses_injected_audit_and_provenance_objects() -> None:
    audit = FakeAuditSink()
    provenance = FakeProvenance()
    service_bundle = bundle()
    service = SelfAssessmentService(
        service_bundle.repository,
        service_bundle.policy,
        profile_service=service_bundle.profile,
        capability_awareness_service=service_bundle.capabilities,
        limitation_service=service_bundle.limitations,
        settings=service_bundle.settings,
        audit_sink=audit,
        provenance_service=provenance,
    )

    service.run(SelfAssessmentRequest(owner_scope=["workspace:main"]))

    assert audit.events
    assert provenance.links
