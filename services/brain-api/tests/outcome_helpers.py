"""Shared helpers for outcome tests."""

from __future__ import annotations

from aion_brain.contracts.policy import PolicyDecision, PolicyRequest
from aion_brain.outcomes.attribution import CausalAttributionService
from aion_brain.outcomes.collector import ObservedEffectCollector
from aion_brain.outcomes.effects import ExpectedEffectService
from aion_brain.outcomes.feedback import OutcomeFeedbackService
from aion_brain.outcomes.query import OutcomeQueryService
from aion_brain.outcomes.repository import OutcomeRepository
from aion_brain.outcomes.service import OutcomeService
from aion_brain.outcomes.verifier import EffectVerifier


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
            reason="denied",
            constraints=[],
            audit_level="standard",
        )


class TelemetrySink:
    def __init__(self) -> None:
        self.events: list[object] = []

    def emit(self, event: object) -> None:
        self.events.append(event)


class ProvenanceSink:
    def __init__(self) -> None:
        self.links: list[tuple[str, str, str]] = []

    def create_link(self, source_id: str, target_id: str, relation_type: str) -> None:
        self.links.append((source_id, target_id, relation_type))


class Settings:
    outcome_min_verified_score = 0.75
    outcome_auto_collect_from_commands = True
    outcome_auto_collect_from_workflows = True
    outcome_auto_verify_enabled = False


class OutcomeBundle:
    def __init__(self, policy: object | None = None) -> None:
        self.repository = OutcomeRepository()
        self.policy = policy or AllowPolicy()
        self.telemetry = TelemetrySink()
        self.provenance = ProvenanceSink()
        self.settings = Settings()
        self.expected = ExpectedEffectService(
            self.repository,
            self.policy,
            telemetry_service=self.telemetry,
            provenance_service=self.provenance,
        )
        self.observed = ObservedEffectCollector(
            self.repository,
            self.policy,
            telemetry_service=self.telemetry,
        )
        self.outcomes = OutcomeService(
            self.repository,
            self.policy,
            telemetry_service=self.telemetry,
            provenance_service=self.provenance,
            settings=self.settings,
        )
        self.verifier = EffectVerifier(
            self.repository,
            self.policy,
            observed_effect_collector=self.observed,
            telemetry_service=self.telemetry,
            provenance_service=self.provenance,
            settings=self.settings,
        )
        self.attribution = CausalAttributionService(
            self.repository,
            self.policy,
            telemetry_service=self.telemetry,
            provenance_service=self.provenance,
        )
        self.feedback = OutcomeFeedbackService(
            self.repository,
            self.policy,
            telemetry_service=self.telemetry,
        )
        self.query = OutcomeQueryService(self.outcomes)


def bundle(policy: object | None = None) -> OutcomeBundle:
    return OutcomeBundle(policy)
