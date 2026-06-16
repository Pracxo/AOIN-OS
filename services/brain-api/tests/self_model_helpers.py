from __future__ import annotations

from types import SimpleNamespace

from aion_brain.contracts.policy import PolicyDecision, PolicyRequest
from aion_brain.self_model.assessment import SelfAssessmentService
from aion_brain.self_model.capability_awareness import CapabilityAwarenessService
from aion_brain.self_model.confidence import ConfidenceCalibrator
from aion_brain.self_model.description import SelfDescriptionService
from aion_brain.self_model.introspection import IntrospectionSnapshotService
from aion_brain.self_model.limitations import LimitationLedgerService
from aion_brain.self_model.profile import SelfModelProfileService
from aion_brain.self_model.repository import SelfModelRepository


class AllowPolicy:
    def __init__(self) -> None:
        self.requests: list[PolicyRequest] = []

    def authorize(self, request: PolicyRequest) -> PolicyDecision:
        self.requests.append(request)
        return PolicyDecision(
            decision_id=f"decision-{request.request_id}",
            trace_id=request.trace_id or "",
            allow=True,
            approval_required=False,
            reason="allowed",
            constraints=[],
            audit_level="standard",
        )


class DenyPolicy:
    def authorize(self, request: PolicyRequest) -> PolicyDecision:
        return PolicyDecision(
            decision_id=f"decision-{request.request_id}",
            trace_id=request.trace_id or "",
            allow=False,
            approval_required=False,
            reason="denied_for_test",
            constraints=["denied_for_test"],
            audit_level="high",
        )


class FakeTelemetry:
    def __init__(self) -> None:
        self.events: list[object] = []

    def emit(self, event: object) -> None:
        self.events.append(event)


class FakeAuditSink:
    def __init__(self) -> None:
        self.events: list[tuple[str, dict[str, object]]] = []

    def record(self, event_type: str, payload: dict[str, object]) -> None:
        self.events.append((event_type, payload))


class FakeProvenance:
    def __init__(self) -> None:
        self.links: list[dict[str, object]] = []

    def create_link(self, **kwargs: object) -> None:
        self.links.append(kwargs)


def settings() -> SimpleNamespace:
    return SimpleNamespace(
        aion_release_version="0.1.0",
        version="0.1.0",
        env="test",
        self_model_enabled=True,
        capability_awareness_enabled=True,
        limitation_ledger_enabled=True,
        confidence_calibration_enabled=True,
        introspection_snapshots_enabled=True,
        self_assessment_enabled=True,
        self_description_include_limitations_default=True,
        confidence_low_threshold=0.4,
        confidence_high_threshold=0.75,
        model_gateway_enabled=False,
        turbovec_enabled=False,
        graphiti_enabled=False,
        sandbox_execution_enabled=False,
        backup_restore_apply_enabled=False,
        workflow_controlled_execution_enabled=False,
        observability_adapter="local",
    )


def bundle(
    policy: object | None = None,
    *,
    settings_obj: object | None = None,
) -> SimpleNamespace:
    repository = SelfModelRepository()
    policy_adapter = policy or AllowPolicy()
    telemetry = FakeTelemetry()
    audit = FakeAuditSink()
    provenance = FakeProvenance()
    configured_settings = settings_obj or settings()
    capabilities = CapabilityAwarenessService(
        repository,
        policy_adapter,
        settings=configured_settings,
        telemetry_service=telemetry,
    )
    limitations = LimitationLedgerService(
        repository,
        policy_adapter,
        telemetry_service=telemetry,
        audit_sink=audit,
    )
    profile = SelfModelProfileService(
        repository,
        policy_adapter,
        capability_awareness_service=capabilities,
        limitation_service=limitations,
        settings=configured_settings,
        telemetry_service=telemetry,
    )
    confidence = ConfidenceCalibrator(
        repository,
        policy_adapter,
        settings=configured_settings,
        telemetry_service=telemetry,
        audit_sink=audit,
    )
    assessment = SelfAssessmentService(
        repository,
        policy_adapter,
        profile_service=profile,
        capability_awareness_service=capabilities,
        limitation_service=limitations,
        settings=configured_settings,
        telemetry_service=telemetry,
        audit_sink=audit,
        provenance_service=provenance,
    )
    introspection = IntrospectionSnapshotService(
        repository,
        policy_adapter,
        profile_service=profile,
        capability_awareness_service=capabilities,
        limitation_service=limitations,
        confidence_calibrator=confidence,
        settings=configured_settings,
        telemetry_service=telemetry,
    )
    return SimpleNamespace(
        repository=repository,
        policy=policy_adapter,
        telemetry=telemetry,
        audit=audit,
        provenance=provenance,
        capabilities=capabilities,
        limitations=limitations,
        profile=profile,
        description=SelfDescriptionService(profile),
        confidence=confidence,
        assessment=assessment,
        introspection=introspection,
        settings=configured_settings,
    )
