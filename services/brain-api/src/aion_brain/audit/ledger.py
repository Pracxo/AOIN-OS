"""Audit ledger service."""

from aion_brain.audit.repository import AuditRepository
from aion_brain.contracts.evaluation import EvaluationRecord
from aion_brain.contracts.learning import LearningSignal
from aion_brain.contracts.policy import PolicyDecision
from aion_brain.contracts.telemetry import VisualTelemetryEvent
from aion_brain.contracts.traces import DecisionTrace


class AuditLedger:
    """Records Brain loop artifacts through the audit repository."""

    def __init__(self, repository: AuditRepository) -> None:
        self._repository = repository

    def record(self, trace: DecisionTrace) -> str:
        """Record a decision trace and return its ID."""
        self._repository.save_trace(trace)
        return trace.trace_id

    def record_policy_decisions(
        self,
        trace_id: str,
        decisions: list[PolicyDecision],
    ) -> list[PolicyDecision]:
        """Record policy decisions for a trace."""
        return self._repository.save_policy_decisions(trace_id, decisions)

    def record_evaluation(self, evaluation: EvaluationRecord) -> EvaluationRecord:
        """Record an evaluation."""
        return self._repository.save_evaluation(evaluation)

    def record_learning_signal(self, signal: LearningSignal) -> LearningSignal:
        """Record a learning signal candidate."""
        return self._repository.save_learning_signal(signal)

    def record_visual_telemetry(
        self,
        trace_id: str,
        events: list[VisualTelemetryEvent],
    ) -> list[VisualTelemetryEvent]:
        """Record visual telemetry events for a trace."""
        return self._repository.save_visual_telemetry(trace_id, events)

    def get_trace(self, trace_id: str) -> DecisionTrace | None:
        """Return a decision trace through the audit boundary."""
        return self._repository.get_trace(trace_id)

    def list_visual_telemetry(self, trace_id: str) -> list[VisualTelemetryEvent]:
        """Return visual telemetry through the audit boundary."""
        return self._repository.list_visual_telemetry(trace_id)
