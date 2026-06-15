"""Brain loop reflection and skill candidate guardrail tests."""

from datetime import UTC, datetime

from aion_brain.contracts.evaluation import EvaluationRecord
from aion_brain.contracts.events import AIONEvent
from aion_brain.contracts.learning import LearningSignal
from aion_brain.contracts.policy import PolicyDecision
from aion_brain.contracts.reflection import ReflectionRecord, ReflectionRequest
from aion_brain.contracts.skills import SkillCandidate
from aion_brain.contracts.state import BrainState
from aion_brain.contracts.telemetry import VisualTelemetryEvent
from aion_brain.contracts.traces import DecisionTrace
from aion_brain.core.brain_loop import BrainLoopService
from aion_brain.evaluation.evaluator import Evaluator
from aion_brain.learning.engine import LearningEngine
from aion_brain.telemetry.visual import VisualTelemetryBuilder
from tests.test_skill_service import make_candidate


class FakeRuntime:
    """Runtime fake."""

    def run_state(self, event: AIONEvent) -> BrainState:
        return BrainState(
            event=event,
            trace=DecisionTrace(
                trace_id=event.trace_id or "trace-1",
                event_id=event.event_id,
                intent_id="intent-1",
                context_id="context-1",
                plan_id="plan-1",
                memory_refs=[],
                capability_refs=[],
                policy_decisions=[],
                outcome={"status": "planned"},
                created_at=datetime.now(UTC),
            ),
            policy_decisions=[],
            status="planned",
        )


class FakeAuditLedger:
    """Audit fake."""

    def record(self, trace: DecisionTrace) -> DecisionTrace:
        return trace

    def record_policy_decisions(
        self,
        trace_id: str,
        decisions: list[PolicyDecision],
    ) -> None:
        return None

    def record_evaluation(self, evaluation: EvaluationRecord) -> EvaluationRecord:
        return evaluation

    def record_learning_signal(self, signal: LearningSignal) -> LearningSignal:
        return signal

    def record_visual_telemetry(
        self,
        trace_id: str,
        events: list[VisualTelemetryEvent],
    ) -> None:
        return None


class FakeReflectionEngine:
    """Reflection engine fake."""

    def __init__(self) -> None:
        self.calls = 0

    def reflect(self, request: ReflectionRequest) -> ReflectionRecord:
        self.calls += 1
        return ReflectionRecord(
            reflection_id="reflection-1",
            trace_id=request.trace.trace_id if request.trace else None,
            learning_signal_ids=[signal.learning_id for signal in request.learning_signals],
            reflection_type="trace_review",
            observations=["successful_plan_pattern_observed"],
            proposed_changes=[],
            risks=[],
            confidence=0.7,
            status="recorded",
            created_at=datetime.now(UTC),
        )


class FakeSkillService:
    """Skill service fake."""

    def __init__(self) -> None:
        self.candidate_calls = 0
        self.promote_calls = 0

    def create_candidate_from_reflection(self, reflection_id: str) -> SkillCandidate:
        self.candidate_calls += 1
        return make_candidate()

    def promote_candidate(self, request: object) -> object:
        self.promote_calls += 1
        raise AssertionError("brain think must not promote skills")


def test_brain_think_does_not_reflect_unless_payload_reflect_is_true() -> None:
    """Reflection is opt-in from /brain/think payload."""
    reflection_engine = FakeReflectionEngine()
    skill_service = FakeSkillService()
    trace = make_service(reflection_engine, skill_service).think(make_event({"question": "what?"}))

    assert "reflection_id" not in trace.outcome
    assert reflection_engine.calls == 0
    assert skill_service.candidate_calls == 0
    assert skill_service.promote_calls == 0


def test_brain_think_reflects_without_candidate_by_default() -> None:
    """Reflect=true creates reflection metadata but no skill candidate."""
    reflection_engine = FakeReflectionEngine()
    skill_service = FakeSkillService()
    trace = make_service(reflection_engine, skill_service).think(
        make_event({"question": "what?", "reflect": True})
    )

    assert trace.outcome["reflection_id"] == "reflection-1"
    assert "candidate_id" not in trace.outcome
    assert reflection_engine.calls == 1
    assert skill_service.candidate_calls == 0


def test_brain_think_creates_candidate_only_with_explicit_flag_and_never_promotes() -> None:
    """Skill candidate creation is explicit and promotion is unavailable from think."""
    reflection_engine = FakeReflectionEngine()
    skill_service = FakeSkillService()
    trace = make_service(reflection_engine, skill_service).think(
        make_event({"question": "what?", "reflect": True, "create_skill_candidate": True})
    )

    assert trace.outcome["reflection_id"] == "reflection-1"
    assert trace.outcome["candidate_id"] == "candidate-1"
    assert skill_service.candidate_calls == 1
    assert skill_service.promote_calls == 0


def make_service(
    reflection_engine: FakeReflectionEngine,
    skill_service: FakeSkillService,
) -> BrainLoopService:
    """Create a BrainLoopService with fakes."""
    return BrainLoopService(
        runtime=FakeRuntime(),  # type: ignore[arg-type]
        audit_ledger=FakeAuditLedger(),  # type: ignore[arg-type]
        evaluator=Evaluator(),
        learning_engine=LearningEngine(),
        telemetry_builder=VisualTelemetryBuilder(),
        reflection_engine=reflection_engine,  # type: ignore[arg-type]
        skill_service=skill_service,  # type: ignore[arg-type]
    )


def make_event(payload: dict[str, object]) -> AIONEvent:
    """Create a normalized event."""
    return AIONEvent(
        event_id="event-1",
        source="test",
        event_type="question.answer",
        payload_type="test.payload",
        payload=payload,
        timestamp=datetime.now(UTC),
        trace_id="trace-1",
        security_scope=["workspace:main"],
    )
