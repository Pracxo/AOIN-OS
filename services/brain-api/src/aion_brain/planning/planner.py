"""Deterministic AION planner."""

from aion_brain.contracts.context import ContextPacket
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

        return PlanGraph(
            plan_id=f"plan-{context.intent_id}",
            intent_id=context.intent_id,
            goal=context.goal,
            steps=steps,
            dependencies=[],
            risk_level=risk_level,
            approval_required=risk_level == "high",
            status="draft",
            metadata=_metadata(reasoning, skills),
        )


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
