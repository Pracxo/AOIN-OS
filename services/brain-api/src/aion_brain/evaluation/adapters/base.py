"""Evaluation adapter interface."""

from typing import Protocol

from aion_brain.contracts.regression import EvalAdapterRunRequest, EvalAdapterRunResult


class EvaluationAdapter(Protocol):
    """Boundary for optional future evaluation systems."""

    def run(self, request: EvalAdapterRunRequest) -> EvalAdapterRunResult: ...
