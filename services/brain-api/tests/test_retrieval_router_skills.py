"""Retrieval Router skill registry tests."""

from aion_brain.contracts.policy import PolicyDecision, PolicyRequest
from aion_brain.contracts.retrieval import RetrievalRequest
from aion_brain.contracts.skills import SkillMatchRequest, SkillMatchResult
from aion_brain.retrieval.router import RetrievalRouter
from tests.test_skill_service import make_skill


class FakePolicyAdapter:
    """Policy fake for retrieval tests."""

    def authorize(self, request: PolicyRequest) -> PolicyDecision:
        return PolicyDecision(
            decision_id=f"decision-{request.action_type}",
            trace_id=request.trace_id or "",
            allow=True,
            approval_required=False,
            reason="allowed",
            constraints=[],
            audit_level="standard",
        )


class FakeSkillMatcher:
    """Skill matcher fake."""

    def match(self, request: SkillMatchRequest) -> list[SkillMatchResult]:
        return [
            SkillMatchResult(
                skill=make_skill(status="active"),
                score=0.8,
                matched_patterns=["question.answer"],
                reason="deterministic_token_overlap",
            )
        ]


class FakeTelemetry:
    """Telemetry fake."""

    def __init__(self) -> None:
        self.events: list[object] = []

    def emit(self, event: object) -> None:
        self.events.append(event)


def test_retrieval_router_can_include_skill_registry_results() -> None:
    """Skill registry retrieval returns procedural context items."""
    telemetry = FakeTelemetry()
    result = RetrievalRouter(
        policy_adapter=FakePolicyAdapter(),
        skill_matcher=FakeSkillMatcher(),
        telemetry_service=telemetry,
    ).retrieve(
        RetrievalRequest(
            retrieval_id="retrieval-1",
            trace_id="trace-1",
            intent_id="intent-1",
            query="question plan",
            scope=["workspace:main"],
            requested_sources=["skill_registry"],
        )
    )

    assert result.items[0].source == "skill_registry"
    assert result.items[0].memory_type == "procedural"
    assert result.items[0].source_id == "skill-1"
    assert telemetry.events[0].event_type == "skill_node_seen"
