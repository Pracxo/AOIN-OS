"""Deterministic AION planner."""

from aion_brain.contracts.context import ContextPacket
from aion_brain.contracts.decisions import DecisionFrameCreateRequest
from aion_brain.contracts.effects import ExpectedEffectCreateRequest
from aion_brain.contracts.planning import PlanGraph, PlanStep
from aion_brain.contracts.reasoning import ReasoningResult
from aion_brain.contracts.skills import SkillMatchResult

PLAN_STEP_IDS = {
    "question.answer": ["retrieve_context", "draft_response", "evaluate_response"],
    "goal.plan": ["retrieve_context", "identify_capabilities", "create_plan", "policy_check"],
    "action.execute": [
        "retrieve_context",
        "identify_capabilities",
        "create_plan",
        "policy_check",
        "wait_for_execution_layer",
    ],
    "memory.remember": ["validate_memory_candidate", "policy_check", "store_memory"],
    "memory.retrieve": ["policy_check", "retrieve_memory"],
    "capability.discover": ["policy_check", "list_capabilities"],
    "unknown": ["ask_clarifying_question"],
}

STEP_ACTIONS = {
    "retrieve_context": "memory.retrieve",
    "draft_response": "response.draft",
    "evaluate_response": "evaluation.score",
    "identify_capabilities": "capability.list",
    "create_plan": "plan.create",
    "policy_check": "plan.create",
    "wait_for_execution_layer": "plan.create",
    "validate_memory_candidate": "memory.write",
    "store_memory": "memory.write",
    "retrieve_memory": "memory.retrieve",
    "list_capabilities": "capability.list",
    "ask_clarifying_question": "clarification.ask",
}

INTENT_RISKS = {
    "question.answer": "low",
    "goal.plan": "medium",
    "action.execute": "high",
    "memory.remember": "medium",
    "memory.retrieve": "low",
    "capability.discover": "low",
    "unknown": "medium",
}


class Planner:
    """Create generic deterministic plans from context packets."""

    def __init__(
        self,
        decision_frame_service: object | None = None,
        expected_effect_service: object | None = None,
    ) -> None:
        self._decision_frame_service = decision_frame_service
        self._expected_effect_service = expected_effect_service

    def create_plan(
        self,
        context: ContextPacket,
        reasoning: ReasoningResult | None = None,
        skills: list[SkillMatchResult] | None = None,
    ) -> PlanGraph:
        """Create a policy-checkable plan graph."""
        intent_type = _intent_type(context)
        step_ids = list(PLAN_STEP_IDS.get(intent_type, PLAN_STEP_IDS["unknown"]))
        if reasoning is not None and reasoning.requires_clarification:
            if "ask_clarifying_question" not in step_ids:
                step_ids.append("ask_clarifying_question")
        risk_level = INTENT_RISKS.get(intent_type, "medium")
        steps = [
            PlanStep(
                step_id=step_id,
                action_type=STEP_ACTIONS[step_id],
                capability_required=STEP_ACTIONS[step_id],
                risk_level=risk_level,
                status="pending",
            )
            for step_id in step_ids
        ]

        metadata = _metadata(reasoning, skills)
        if context.execution_limits.get("create_decision_frame") is True:
            frame_id = _maybe_create_decision_frame(self._decision_frame_service, context)
            if frame_id:
                metadata["decision_frame_id"] = frame_id

        plan = PlanGraph(
            plan_id=f"plan-{context.intent_id}",
            intent_id=context.intent_id,
            goal=context.goal,
            steps=steps,
            dependencies=[],
            risk_level=risk_level,
            approval_required=risk_level == "high",
            status="draft",
            metadata=metadata,
        )
        if context.execution_limits.get("create_expected_effects") is True:
            _maybe_create_expected_effects(self._expected_effect_service, plan, context)
        return plan


def _intent_type(context: ContextPacket) -> str:
    for item in context.known_context:
        value = item.get("intent_type")
        if isinstance(value, str):
            return value
    return "unknown"


def _metadata(
    reasoning: ReasoningResult | None,
    skills: list[SkillMatchResult] | None,
) -> dict[str, object]:
    metadata: dict[str, object] = {}
    if reasoning is not None and reasoning.suggested_next_actions:
        metadata["reasoning_suggested_next_actions"] = list(reasoning.suggested_next_actions)
    if skills:
        metadata["matched_skill_ids"] = [result.skill.skill_id for result in skills]
    return metadata


def _maybe_create_decision_frame(service: object | None, context: ContextPacket) -> str | None:
    create_frame = getattr(service, "create_frame", None)
    if not callable(create_frame):
        return None
    try:
        frame = create_frame(
            DecisionFrameCreateRequest(
                frame_type="plan_choice",
                title="Plan choice",
                question=f"Which plan should satisfy: {context.goal}",
                owner_scope=_scope(context),
                constraints=list(context.constraints),
                metadata={"source": "planner", "create_decision_frame": True},
            )
        )
    except Exception:
        return None
    return str(getattr(frame, "decision_frame_id", "")) or None


def _scope(context: ContextPacket) -> list[str]:
    raw = context.execution_limits.get("owner_scope") or context.execution_limits.get("scope")
    if isinstance(raw, list) and raw:
        return [str(item) for item in raw]
    return ["workspace:main"]


def _trace_id(context: ContextPacket) -> str | None:
    raw = context.execution_limits.get("trace_id")
    return raw if isinstance(raw, str) else None


def _maybe_create_expected_effects(
    service: object | None,
    plan: PlanGraph,
    context: ContextPacket,
) -> None:
    create = getattr(service, "create_expected_effect", None)
    if not callable(create):
        return
    for step in plan.steps:
        try:
            create(
                ExpectedEffectCreateRequest(
                    trace_id=_trace_id(context),
                    source_type="plan",
                    source_id=plan.plan_id,
                    effect_type="generic",
                    predicate="plan_step_expected",
                    object_ref=step.step_id,
                    expected_value={"step_id": step.step_id, "status": "pending"},
                    success_criteria={"exists": True},
                    required=True,
                    confidence=0.5,
                    owner_scope=_scope(context),
                    metadata={
                        "source": "planner",
                        "action_type": step.action_type,
                        "capability_required": step.capability_required,
                    },
                )
            )
        except Exception:
            continue
