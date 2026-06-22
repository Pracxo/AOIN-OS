from __future__ import annotations

from types import SimpleNamespace

from aion_brain.beliefs.claim_extractor import ClaimExtractor
from aion_brain.beliefs.contradictions import BeliefContradictionService
from aion_brain.beliefs.query import BeliefQueryService
from aion_brain.beliefs.repository import BeliefRepository
from aion_brain.beliefs.service import BeliefService
from aion_brain.beliefs.supports import BeliefSupportService
from aion_brain.beliefs.truth_maintenance import TruthMaintenanceService
from aion_brain.contracts.beliefs import BeliefClaimCreateRequest
from aion_brain.contracts.policy import PolicyDecision, PolicyRequest


class AllowPolicy:
    def authorize(self, request: PolicyRequest) -> PolicyDecision:
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
            constraints=["test"],
            audit_level="high",
        )


class FakeTelemetry:
    def __init__(self) -> None:
        self.events: list[object] = []

    def emit(self, event: object) -> None:
        self.events.append(event)


def belief_bundle(policy: object | None = None) -> SimpleNamespace:
    repository = BeliefRepository()
    policy_adapter = policy or AllowPolicy()
    telemetry = FakeTelemetry()
    settings = SimpleNamespace(
        belief_min_supported_confidence=0.65,
        belief_stale_after_days=180,
    )
    service = BeliefService(
        repository,
        policy_adapter,
        telemetry_service=telemetry,
        settings=settings,
    )
    contradictions = BeliefContradictionService(
        repository,
        policy_adapter,
        telemetry_service=telemetry,
    )
    supports = BeliefSupportService(
        repository,
        policy_adapter,
        contradiction_service=contradictions,
        telemetry_service=telemetry,
    )
    query = BeliefQueryService(repository, policy_adapter, telemetry_service=telemetry)
    truth = TruthMaintenanceService(
        repository,
        policy_adapter,
        telemetry_service=telemetry,
        settings=settings,
    )
    return SimpleNamespace(
        repository=repository,
        policy=policy_adapter,
        telemetry=telemetry,
        service=service,
        supports=supports,
        contradictions=contradictions,
        query=query,
        truth=truth,
        extractor=ClaimExtractor(),
    )


def create_claim(
    bundle: SimpleNamespace,
    text: str = "The local system is ready",
    *,
    confidence: float = 0.7,
    evidence_refs: list[str] | None = None,
    source_id: str | None = "source-1",
) -> object:
    return bundle.service.create_claim(
        BeliefClaimCreateRequest(
            claim_text=text,
            claim_type="generic",
            source_type="generic",
            source_id=source_id,
            owner_scope=["workspace:main"],
            confidence=confidence,
            evidence_refs=evidence_refs or [],
        )
    )
