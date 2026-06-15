"""Promptfoo placeholder boundary."""

from aion_brain.contracts.regression import EvalAdapterRunRequest, EvalAdapterRunResult


class PromptfooAdapter:
    """Promptfoo is planned as AION's prompt and regression evaluation adapter.

    AION contracts must remain independent of Promptfoo internals.
    """

    def run(self, request: EvalAdapterRunRequest) -> EvalAdapterRunResult:
        """Reject use until a future task explicitly enables the adapter."""
        raise NotImplementedError("promptfoo_adapter_not_implemented")
