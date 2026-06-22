"""Ragas placeholder boundary."""

from aion_brain.contracts.regression import EvalAdapterRunRequest, EvalAdapterRunResult


class RagasAdapter:
    """Ragas is planned as AION's retrieval and RAG evaluation adapter.

    AION contracts must remain independent of Ragas internals.
    """

    def run(self, request: EvalAdapterRunRequest) -> EvalAdapterRunResult:
        """Reject use until a future task explicitly enables the adapter."""
        raise NotImplementedError("ragas_adapter_not_implemented")
