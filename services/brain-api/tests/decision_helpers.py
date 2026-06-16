"""Shared helpers for decision intelligence tests."""

from __future__ import annotations

from aion_brain.contracts.policy import PolicyDecision, PolicyRequest
from aion_brain.decisions.counterfactuals import CounterfactualSimulator
from aion_brain.decisions.evaluator import OptionEvaluator
from aion_brain.decisions.frames import DecisionFrameService
from aion_brain.decisions.journal import DecisionJournalService
from aion_brain.decisions.options import DecisionOptionService
from aion_brain.decisions.recommendations import DecisionRecommendationService
from aion_brain.decisions.repository import DecisionRepository
from aion_brain.decisions.tradeoffs import TradeoffMatrixService
from aion_brain.decisions.utility import UtilityProfileService


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


class Settings:
    decision_controlled_mode_enabled = False
    counterfactuals_enabled = True
    decision_auto_commit_enabled = False


class DecisionBundle:
    def __init__(self, policy: object | None = None) -> None:
        self.repository = DecisionRepository()
        self.policy = policy or AllowPolicy()
        self.telemetry = TelemetrySink()
        self.settings = Settings()
        self.frame_service = DecisionFrameService(
            self.repository,
            self.policy,
            telemetry_service=self.telemetry,
        )
        self.option_service = DecisionOptionService(
            self.repository,
            self.policy,
            telemetry_service=self.telemetry,
        )
        self.utility_service = UtilityProfileService(
            self.repository,
            self.policy,
            telemetry_service=self.telemetry,
        )
        self.tradeoff_service = TradeoffMatrixService(
            self.repository,
            telemetry_service=self.telemetry,
        )
        self.evaluator = OptionEvaluator(
            self.repository,
            self.policy,
            self.utility_service,
            self.tradeoff_service,
            telemetry_service=self.telemetry,
            settings=self.settings,
        )
        self.counterfactuals = CounterfactualSimulator(
            self.repository,
            self.policy,
            telemetry_service=self.telemetry,
            settings=self.settings,
        )
        self.journal = DecisionJournalService(
            self.repository,
            self.policy,
            telemetry_service=self.telemetry,
        )
        self.recommendations = DecisionRecommendationService(
            self.repository,
            self.option_service,
            self.evaluator,
            self.counterfactuals,
            settings=self.settings,
        )


def bundle(policy: object | None = None) -> DecisionBundle:
    return DecisionBundle(policy)
