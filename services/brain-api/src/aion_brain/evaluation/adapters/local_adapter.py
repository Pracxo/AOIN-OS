"""Local deterministic evaluation adapter."""

from aion_brain.contracts.regression import EvalAdapterRunRequest, EvalAdapterRunResult


class LocalEvaluationAdapter:
    """Return a local-only evaluation summary without external calls."""

    def run(self, request: EvalAdapterRunRequest) -> EvalAdapterRunResult:
        """Return a stable local evaluation result."""
        return EvalAdapterRunResult(
            adapter_name="local",
            status="completed",
            output={
                "regression_run_id": request.regression_run_id,
                "dataset_ref": request.dataset_ref,
                "config_keys": sorted(request.config),
                "external_calls": False,
            },
            reason=None,
        )
