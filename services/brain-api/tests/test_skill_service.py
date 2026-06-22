"""Skill service and promotion tests."""

from datetime import UTC, datetime

import pytest

from aion_brain.contracts.policy import PolicyDecision, PolicyRequest
from aion_brain.contracts.reflection import ReflectionRecord
from aion_brain.contracts.skills import (
    SkillActivationEvent,
    SkillActivationRequest,
    SkillCandidate,
    SkillProcedureStep,
    SkillPromotionRequest,
    SkillRecord,
    SkillVersion,
)
from aion_brain.contracts.telemetry import VisualTelemetryEvent
from aion_brain.skills.promotion import SkillCandidateBuilder
from aion_brain.skills.service import SkillService, can_transition_skill


class FakePolicyAdapter:
    """Policy fake for skill tests."""

    def __init__(self, *, deny_actions: set[str] | None = None) -> None:
        self.deny_actions = deny_actions or set()
        self.requests: list[PolicyRequest] = []

    def authorize(self, request: PolicyRequest) -> PolicyDecision:
        self.requests.append(request)
        allow = request.action_type not in self.deny_actions
        return PolicyDecision(
            decision_id=f"decision-{request.action_type}",
            trace_id=request.trace_id or "",
            allow=allow,
            approval_required=False,
            reason="allowed" if allow else "denied",
            constraints=[],
            audit_level="standard",
        )


class FakeReflectionRepository:
    """Reflection repository fake."""

    def __init__(self, reflection: ReflectionRecord | None = None) -> None:
        self.reflection = reflection or make_reflection()

    def get_reflection(self, reflection_id: str) -> ReflectionRecord | None:
        if reflection_id == self.reflection.reflection_id:
            return self.reflection
        return None


class FakeSkillRepository:
    """Skill repository fake."""

    def __init__(self) -> None:
        self.candidates: dict[str, SkillCandidate] = {}
        self.skills: dict[str, SkillRecord] = {}
        self.versions: list[SkillVersion] = []
        self.events: list[SkillActivationEvent] = []

    def save_candidate(self, candidate: SkillCandidate) -> SkillCandidate:
        self.candidates[candidate.candidate_id] = candidate
        return candidate

    def get_candidate(self, candidate_id: str) -> SkillCandidate | None:
        return self.candidates.get(candidate_id)

    def list_candidates(
        self,
        *,
        status: str | None = None,
        limit: int = 50,
    ) -> list[SkillCandidate]:
        candidates = [
            candidate
            for candidate in self.candidates.values()
            if status is None or candidate.status == status
        ]
        return candidates[:limit]

    def save_skill(self, skill: SkillRecord) -> SkillRecord:
        self.skills[skill.skill_id] = skill
        return skill

    def get_skill(self, skill_id: str) -> SkillRecord | None:
        return self.skills.get(skill_id)

    def list_skills(
        self,
        *,
        scope: list[str],
        status: str | None = None,
        limit: int = 50,
    ) -> list[SkillRecord]:
        skills = [
            skill
            for skill in self.skills.values()
            if (status is None or skill.status == status)
            and any(item in skill.owner_scope for item in scope)
        ]
        return skills[:limit]

    def save_version(self, version: SkillVersion) -> SkillVersion:
        self.versions.append(version)
        return version

    def save_activation_event(self, event: SkillActivationEvent) -> SkillActivationEvent:
        self.events.append(event)
        return event


class FakeTelemetry:
    """Telemetry fake."""

    def __init__(self) -> None:
        self.events: list[VisualTelemetryEvent] = []

    def emit(self, event: VisualTelemetryEvent) -> None:
        self.events.append(event)


def test_skill_candidate_builder_creates_candidate_from_generic_reflection() -> None:
    """Generic reflection procedures become skill candidates."""
    candidate = SkillCandidateBuilder().build(make_reflection())

    assert candidate is not None
    assert candidate.status == "candidate"
    assert candidate.name == "Generic planning procedure"
    assert [step.action_type for step in candidate.procedure_steps] == [
        "retrieve_context",
        "compile_context",
        "create_plan",
        "policy_check",
    ]


def test_skill_candidate_builder_rejects_weak_evidence() -> None:
    """Weak reflection evidence does not create a candidate."""
    reflection = make_reflection(confidence=0.4)

    assert SkillCandidateBuilder().build(reflection) is None


def test_skill_service_lists_and_updates_candidates() -> None:
    """SkillService lists and updates candidate review status."""
    repository = FakeSkillRepository()
    repository.save_candidate(make_candidate())
    service = make_service(repository)

    listed = service.list_candidates(status="candidate")
    updated = service.update_candidate_status("candidate-1", "approved", "reviewed")

    assert listed[0].candidate_id == "candidate-1"
    assert updated.status == "approved"
    assert repository.candidates["candidate-1"].status == "approved"


def test_promotion_rejects_candidate_below_confidence_threshold() -> None:
    """Promotion requires candidate confidence >= 0.65."""
    repository = FakeSkillRepository()
    repository.save_candidate(make_candidate(confidence=0.6, status="approved"))

    response = make_service(repository).promote_candidate(make_promotion_request())

    assert response.promoted is False
    assert response.reason == "candidate_confidence_below_threshold"


def test_promotion_rejects_candidate_without_source_evidence() -> None:
    """Promotion requires source traces or tasks."""
    repository = FakeSkillRepository()
    repository.save_candidate(
        make_candidate(source_trace_ids=[], source_task_ids=[], status="approved")
    )

    response = make_service(repository).promote_candidate(make_promotion_request())

    assert response.promoted is False
    assert response.reason == "candidate_missing_source_evidence"


def test_promotion_creates_skill_version_and_draft_by_default() -> None:
    """Promotion creates a draft skill and version without automatic activation."""
    repository = FakeSkillRepository()
    repository.save_candidate(make_candidate(status="approved"))
    telemetry = FakeTelemetry()

    response = make_service(repository, telemetry=telemetry).promote_candidate(
        make_promotion_request()
    )

    assert response.promoted is True
    assert response.status == "draft"
    assert response.skill_id in repository.skills
    assert repository.versions[0].version == 1
    assert repository.candidates["candidate-1"].status == "promoted"
    assert telemetry.events[0].event_type == "skill_promoted"


def test_promotion_activates_only_when_requested_and_policy_allows() -> None:
    """Activation during promotion requires explicit request and policy allow."""
    repository = FakeSkillRepository()
    repository.save_candidate(make_candidate(status="approved"))

    response = make_service(repository).promote_candidate(make_promotion_request(activate=True))

    assert response.promoted is True
    assert response.status == "active"
    assert repository.events[-1].event_type == "skill_activated"


def test_high_risk_skill_activation_requires_policy_approval() -> None:
    """Policy denial blocks high-risk skill activation."""
    repository = FakeSkillRepository()
    repository.save_skill(make_skill(risk_level="high", status="draft"))
    service = make_service(repository, policy=FakePolicyAdapter(deny_actions={"skill.activate"}))

    with pytest.raises(ValueError, match="policy_denied"):
        service.transition_skill(
            SkillActivationRequest(
                skill_id="skill-1",
                to_status="active",
                reason="activate",
            )
        )


def test_skill_transition_state_machine_rejects_invalid_transition() -> None:
    """Skill status transitions are constrained."""
    assert can_transition_skill("active", "draft") is False
    repository = FakeSkillRepository()
    repository.save_skill(make_skill(status="active"))

    with pytest.raises(ValueError, match="invalid_skill_transition"):
        make_service(repository).transition_skill(
            SkillActivationRequest(skill_id="skill-1", to_status="draft", reason="no")
        )


def make_service(
    repository: FakeSkillRepository,
    *,
    policy: FakePolicyAdapter | None = None,
    telemetry: FakeTelemetry | None = None,
) -> SkillService:
    """Create a skill service with fakes."""
    return SkillService(
        skill_repository=repository,  # type: ignore[arg-type]
        reflection_repository=FakeReflectionRepository(),
        policy_adapter=policy or FakePolicyAdapter(),
        telemetry_service=telemetry,
    )


def make_reflection(confidence: float = 0.75) -> ReflectionRecord:
    """Create a generic reflection record."""
    return ReflectionRecord(
        reflection_id="reflection-1",
        trace_id="trace-1",
        learning_signal_ids=["learning-1"],
        reflection_type="trace_review",
        observations=["successful_plan_pattern_observed"],
        proposed_changes=[
            {
                "change_type": "generic_procedure",
                "name": "Generic planning procedure",
                "description": "Reuse a reviewed generic Brain procedure as procedural memory.",
                "trigger_patterns": ["question.answer", "plan.create"],
                "procedure_steps": [
                    "retrieve_context",
                    "compile_context",
                    "create_plan",
                    "policy_check",
                ],
                "expected_outcomes": ["reviewed_generic_procedure_available"],
            }
        ],
        risks=[],
        confidence=confidence,
        status="recorded",
        created_at=datetime.now(UTC),
    )


def make_step() -> SkillProcedureStep:
    """Create a generic skill procedure step."""
    return SkillProcedureStep(
        step_id="skill-step-1",
        action_type="retrieve_context",
        description="Retrieve context",
        risk_level="low",
        policy_action="memory.retrieve",
    )


def make_candidate(
    *,
    confidence: float = 0.75,
    status: str = "candidate",
    source_trace_ids: list[str] | None = None,
    source_task_ids: list[str] | None = None,
) -> SkillCandidate:
    """Create a skill candidate."""
    return SkillCandidate(
        candidate_id="candidate-1",
        reflection_id="reflection-1",
        source_trace_ids=["trace-1"] if source_trace_ids is None else source_trace_ids,
        source_task_ids=[] if source_task_ids is None else source_task_ids,
        source_learning_signal_ids=["learning-1"],
        name="Generic planning procedure",
        description="Reuse a reviewed generic Brain procedure as procedural memory.",
        trigger_patterns=["question.answer", "plan.create"],
        preconditions=["policy_allows_requested_action"],
        procedure_steps=[make_step()],
        expected_outcomes=["reviewed_generic_procedure_available"],
        risk_level="medium",
        confidence=confidence,
        evaluation_summary={},
        status=status,  # type: ignore[arg-type]
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


def make_skill(
    *,
    candidate_id: str | None = "candidate-1",
    risk_level: str = "medium",
    status: str = "active",
) -> SkillRecord:
    """Create a skill record."""
    return SkillRecord(
        skill_id="skill-1",
        candidate_id=candidate_id,
        name="Generic planning procedure",
        description="Reuse a reviewed generic Brain procedure as procedural memory.",
        status=status,  # type: ignore[arg-type]
        risk_level=risk_level,  # type: ignore[arg-type]
        current_version=1,
        trigger_patterns=["question.answer", "plan.create"],
        preconditions=["policy_allows_requested_action"],
        procedure_steps=[make_step()],
        expected_outcomes=["reviewed_generic_procedure_available"],
        owner_scope=["workspace:main"],
        metadata={},
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


def make_version(skill_id: str = "skill-1", candidate_id: str = "candidate-1") -> SkillVersion:
    """Create a skill version."""
    return SkillVersion(
        skill_version_id="skill-version-1",
        skill_id=skill_id,
        version=1,
        name="Generic planning procedure",
        description="Reuse a reviewed generic Brain procedure as procedural memory.",
        trigger_patterns=["question.answer", "plan.create"],
        preconditions=["policy_allows_requested_action"],
        procedure_steps=[make_step()],
        expected_outcomes=["reviewed_generic_procedure_available"],
        change_reason="approved",
        source_candidate_id=candidate_id,
        created_at=datetime.now(UTC),
    )


def make_promotion_request(activate: bool = False) -> SkillPromotionRequest:
    """Create a promotion request."""
    return SkillPromotionRequest(
        candidate_id="candidate-1",
        actor_id="actor-1",
        owner_scope=["workspace:main"],
        activate=activate,
        reason="approved",
    )
