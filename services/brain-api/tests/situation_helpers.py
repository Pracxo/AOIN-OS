"""Shared helpers for situation model tests."""

from __future__ import annotations

from datetime import UTC, datetime

from aion_brain.contracts.policy import PolicyDecision, PolicyRequest
from aion_brain.situations.continuity import ContextContinuityService
from aion_brain.situations.normalizer import SituationNormalizer
from aion_brain.situations.projector import SituationProjector
from aion_brain.situations.query import SituationQueryService
from aion_brain.situations.repository import SituationRepository
from aion_brain.situations.service import SituationService
from aion_brain.situations.state_atoms import StateAtomService
from aion_brain.situations.temporal_windows import TemporalStateWindowService
from aion_brain.situations.transitions import StateTransitionDetector


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
            reason="denied",
            constraints=[],
            audit_level="standard",
        )


class TelemetrySink:
    def __init__(self) -> None:
        self.events: list[object] = []

    def emit(self, event: object) -> None:
        self.events.append(event)


class SituationBundle:
    def __init__(self, policy: object | None = None) -> None:
        self.repository = SituationRepository()
        self.policy = policy or AllowPolicy()
        self.telemetry = TelemetrySink()
        self.situation_service = SituationService(
            self.repository,
            self.policy,
            telemetry_service=self.telemetry,
        )
        self.state_atom_service = StateAtomService(
            self.repository,
            self.policy,
            telemetry_service=self.telemetry,
        )
        self.transition_detector = StateTransitionDetector()
        self.projector = SituationProjector(
            self.repository,
            self.policy,
            situation_service=self.situation_service,
            state_atom_service=self.state_atom_service,
            normalizer=SituationNormalizer(),
            transition_detector=self.transition_detector,
            telemetry_service=self.telemetry,
        )
        self.temporal_window_service = TemporalStateWindowService(
            self.repository,
            self.policy,
            telemetry_service=self.telemetry,
        )
        self.continuity_service = ContextContinuityService(
            self.repository,
            self.policy,
            telemetry_service=self.telemetry,
        )
        self.query_service = SituationQueryService(self.situation_service)


def now() -> datetime:
    return datetime.now(UTC)


def bundle(policy: object | None = None) -> SituationBundle:
    return SituationBundle(policy)
