"""Local deterministic execution for safe internal Brain steps."""

from datetime import UTC, datetime

from aion_brain.contracts.execution import ExecutionStepRun

SAFE_INTERNAL_STEP_IDS = {
    "retrieve_context",
    "draft_response",
    "evaluate_response",
    "identify_capabilities",
    "create_plan",
    "policy_check",
    "validate_memory_candidate",
    "store_memory",
    "retrieve_memory",
    "list_capabilities",
    "ask_clarifying_question",
    "wait_for_execution_layer",
}


class LocalExecutor:
    """Executes side-effect-free internal generic steps."""

    def execute_step(self, step: ExecutionStepRun) -> ExecutionStepRun:
        """Complete or skip a step deterministically."""
        now = datetime.now(UTC)
        if step.step_id in SAFE_INTERNAL_STEP_IDS:
            return step.model_copy(
                update={
                    "status": "completed",
                    "output": {
                        "executed": True,
                        "action_type": step.step_id,
                        "message": "Generic AION internal step completed.",
                    },
                    "completed_at": now,
                }
            )
        if step.risk_level in {"high", "critical"}:
            return step.model_copy(
                update={
                    "status": "failed",
                    "error": {
                        "reason": (
                            "No executor exists for this high-risk generic action_type in v0.1."
                        )
                    },
                    "completed_at": now,
                }
            )
        return step.model_copy(
            update={
                "status": "skipped",
                "output": {
                    "skipped": True,
                    "reason": "No executor exists for this generic action_type in v0.1.",
                },
                "completed_at": now,
            }
        )
