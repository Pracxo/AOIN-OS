"""Skill candidate building and promotion helpers."""

from datetime import UTC, datetime
from typing import Any, cast
from uuid import uuid4

from aion_brain.contracts.goals import LifecycleRiskLevel
from aion_brain.contracts.reflection import ReflectionRecord
from aion_brain.contracts.skills import SkillCandidate, SkillProcedureAction, SkillProcedureStep

ACTION_POLICY = {
    "retrieve_context": "memory.retrieve",
    "compile_context": "context.compile",
    "reason": "reasoning.run",
    "create_plan": "plan.create",
    "policy_check": "plan.create",
    "dry_run_execute": "plan.execute",
    "evaluate_result": "evaluation.score",
    "record_learning": "learning.record",
    "ask_clarifying_question": "clarification.ask",
}


class SkillCandidateBuilder:
    """Build skill candidates from deterministic reflection data."""

    def build(self, reflection: ReflectionRecord) -> SkillCandidate | None:
        """Create a skill candidate only when evidence supports a generic procedure."""
        change = _generic_procedure_change(reflection)
        if change is None or reflection.confidence < 0.55:
            return None
        source_trace_ids = [reflection.trace_id] if reflection.trace_id else []
        source_task_ids = [reflection.task_id] if reflection.task_id else []
        if not source_trace_ids and not source_task_ids:
            return None
        procedure_actions = _procedure_actions(change)
        if not procedure_actions:
            return None
        now = datetime.now(UTC)
        risk_level = _risk_level(change)
        return SkillCandidate(
            candidate_id=f"candidate-{uuid4().hex}",
            reflection_id=reflection.reflection_id,
            source_trace_ids=source_trace_ids,
            source_task_ids=source_task_ids,
            source_learning_signal_ids=list(reflection.learning_signal_ids),
            name=str(change.get("name") or "Generic procedural memory"),
            description=str(
                change.get("description")
                or "A reviewed generic Brain procedure stored as data."
            ),
            trigger_patterns=_trigger_patterns(change, reflection),
            preconditions=["policy_allows_requested_action"],
            procedure_steps=[
                SkillProcedureStep(
                    step_id=f"skill-step-{index}",
                    action_type=action,
                    description=_description(action),
                    capability_required=None,
                    input_template={},
                    expected_output={},
                    risk_level=risk_level,
                    policy_action=ACTION_POLICY[action],
                )
                for index, action in enumerate(procedure_actions, start=1)
            ],
            expected_outcomes=[
                str(item)
                for item in change.get("expected_outcomes", ["generic_procedure_reused"])
                if isinstance(item, str)
            ],
            risk_level=risk_level,
            confidence=reflection.confidence,
            evaluation_summary={
                "reflection_id": reflection.reflection_id,
                "observations": reflection.observations,
                "risks": reflection.risks,
            },
            status="candidate",
            created_at=now,
            updated_at=now,
        )


def _generic_procedure_change(reflection: ReflectionRecord) -> dict[str, Any] | None:
    for change in reflection.proposed_changes:
        if change.get("change_type") == "generic_procedure":
            return change
    return None


def _procedure_actions(change: dict[str, Any]) -> list[SkillProcedureAction]:
    raw_steps = change.get("procedure_steps")
    if not isinstance(raw_steps, list):
        return []
    return [
        cast(SkillProcedureAction, str(step))
        for step in raw_steps
        if str(step) in ACTION_POLICY
    ]


def _trigger_patterns(change: dict[str, Any], reflection: ReflectionRecord) -> list[str]:
    patterns = [
        str(item)
        for item in change.get("trigger_patterns", [])
        if isinstance(item, str) and item.strip()
    ]
    if not patterns:
        patterns = [reflection.reflection_type]
    return patterns


def _risk_level(change: dict[str, Any]) -> LifecycleRiskLevel:
    value = change.get("risk_level")
    if value in {"low", "medium", "high", "critical"}:
        return cast(LifecycleRiskLevel, value)
    return "medium"


def _description(action: str) -> str:
    return {
        "retrieve_context": "Retrieve relevant context through governed memory boundaries.",
        "compile_context": "Compile a clean context packet.",
        "reason": "Run deterministic generic reasoning.",
        "create_plan": "Create a generic plan graph.",
        "policy_check": "Check policy before continuing.",
        "dry_run_execute": "Validate the plan through dry-run execution.",
        "evaluate_result": "Evaluate the result with deterministic scores.",
        "record_learning": "Record a governed learning signal.",
        "ask_clarifying_question": "Ask for missing context before planning.",
    }[action]
