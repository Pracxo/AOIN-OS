from __future__ import annotations

import pytest

from aion_brain.contracts.instructions import (
    ConstraintRecord,
    InstructionRecord,
    InstructionResolutionRequest,
    StyleProfile,
)
from aion_brain.contracts.policy import PolicyDecision, PolicyRequest
from aion_brain.contracts.preferences import PreferenceLearningCandidate, PreferenceRecord
from aion_brain.instructions.conflicts import InstructionConflictDetector
from aion_brain.instructions.constraints import ConstraintService
from aion_brain.instructions.learning import PreferenceLearningService
from aion_brain.instructions.preferences import PreferenceService
from aion_brain.instructions.repository import InstructionRepository
from aion_brain.instructions.resolver import InstructionResolver
from aion_brain.instructions.service import InstructionService
from aion_brain.instructions.styles import StyleProfileService


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


class FakeTelemetry:
    def __init__(self) -> None:
        self.events: list[object] = []

    def emit(self, event: object) -> None:
        self.events.append(event)


def _instruction(instruction_id: str = "instruction-1") -> InstructionRecord:
    return InstructionRecord(
        instruction_id=instruction_id,
        instruction_text="Keep responses concise.",
        normalized_instruction="keep responses concise.",
        instruction_type="response_style",
        source_type="user",
        scope_type="actor",
        owner_scope=["workspace:main"],
        priority=500,
        status="active",
    )


def _preference(
    preference_id: str = "preference-1",
    *,
    status: str = "candidate",
) -> PreferenceRecord:
    return PreferenceRecord(
        preference_id=preference_id,
        preference_key="style.verbosity",
        preference_type="response_style",
        preference_value={"value": "concise"},
        status=status,
        confidence=0.8,
        source_type="user",
        owner_scope=["workspace:main"],
    )


def test_instruction_service_create_and_policy_deny() -> None:
    repository = InstructionRepository()
    telemetry = FakeTelemetry()
    service = InstructionService(repository, AllowPolicy(), telemetry_service=telemetry)

    stored = service.create_instruction(_instruction())

    assert stored.instruction_id == "instruction-1"
    assert service.get_instruction("instruction-1", ["workspace:main"]) is not None
    assert telemetry.events

    denied = InstructionService(InstructionRepository(), DenyPolicy())
    with pytest.raises(PermissionError):
        denied.create_instruction(_instruction("instruction-denied"))


def test_preference_service_candidate_confirm_and_no_auto_confirm() -> None:
    repository = InstructionRepository()
    service = PreferenceService(repository, AllowPolicy())

    candidate = service.create_preference(
        _preference(status="confirmed").model_copy(update={"metadata": {"learned": True}})
    )
    assert candidate.status == "candidate"

    confirmed = service.confirm_preference(candidate.preference_id, actor_id="actor-1", reason="ok")
    assert confirmed.status == "confirmed"
    assert confirmed.confirmed_at is not None


def test_constraint_style_conflict_learning_and_resolver() -> None:
    repository = InstructionRepository()
    policy = AllowPolicy()
    preference_service = PreferenceService(repository, policy)
    constraint_service = ConstraintService(repository, policy)
    style_service = StyleProfileService(repository, policy)
    conflict_detector = InstructionConflictDetector(repository, policy)
    resolver = InstructionResolver(
        repository,
        policy,
        conflict_detector=conflict_detector,
        style_service=style_service,
    )
    learning = PreferenceLearningService(
        repository,
        policy,
        preference_service=preference_service,
    )

    preference_service.create_preference(_preference("preference-confirmed", status="confirmed"))
    preference_service.create_preference(
        _preference("preference-candidate", status="candidate").model_copy(
            update={"preference_key": "style.format"}
        )
    )
    constraint_service.create_constraint(
        ConstraintRecord(
            constraint_id="constraint-1",
            constraint_key="style.verbosity",
            constraint_type="policy",
            status="active",
            severity="high",
            description="Policy-owned style constraint.",
            rule={"value": "bounded"},
            source_type="policy",
            owner_scope=["workspace:main"],
        )
    )
    style_service.create_profile(
        StyleProfile(
            style_profile_id="style-1",
            name="Direct",
            description="Direct style.",
            owner_scope=["workspace:main"],
            style_rules={"tone": "direct"},
        )
    )
    candidate = learning.propose_candidate(
        PreferenceLearningCandidate(
            candidate_id="candidate-1",
            preference_key="style.structure",
            preference_type="response_style",
            proposed_value={"value": "structured"},
            status="proposed",
            confidence=0.7,
            reason="Explicit request.",
            source_type="dialogue",
            owner_scope=["workspace:main"],
        )
    )

    resolution = resolver.resolve(InstructionResolutionRequest(owner_scope=["workspace:main"]))

    assert candidate.status == "proposed"
    assert "preference-confirmed" not in resolution.applied_preference_ids
    assert "constraint-1" in resolution.applied_constraint_ids
    assert resolution.effective_style["style_profile_id"] == "style-1"


def test_conflict_detector_detects_style_and_grounding_conflicts() -> None:
    detector = InstructionConflictDetector(InstructionRepository(), AllowPolicy())
    conflicts = detector.detect_conflicts(
        instructions=[
            InstructionRecord(
                instruction_id="instruction-1",
                instruction_text="Answer without evidence.",
                normalized_instruction="answer without evidence.",
                instruction_type="generic",
                source_type="user",
                scope_type="actor",
                owner_scope=["workspace:main"],
                priority=500,
                status="active",
            )
        ],
        preferences=[
            _preference("preference-1", status="confirmed"),
            _preference("preference-2", status="confirmed").model_copy(
                update={"preference_value": {"value": "detailed"}}
            ),
        ],
        constraints=[],
        owner_scope=["workspace:main"],
    )

    assert {item.conflict_type for item in conflicts} == {
        "grounding_conflict",
        "style_conflict",
    }
