"""Evaluation adapter boundary tests."""

import pytest

from aion_brain.contracts.regression import EvalAdapterRunRequest
from aion_brain.evaluation.adapters.local_adapter import LocalEvaluationAdapter
from aion_brain.evaluation.adapters.promptfoo_adapter import PromptfooAdapter
from aion_brain.evaluation.adapters.ragas_adapter import RagasAdapter


def test_local_adapter_returns_local_only_summary() -> None:
    """The v0.1 adapter never calls an external evaluator."""
    result = LocalEvaluationAdapter().run(EvalAdapterRunRequest(adapter_name="local", config={}))
    assert result.output["external_calls"] is False


def test_future_eval_adapters_remain_placeholders() -> None:
    """Promptfoo and Ragas remain explicit adapter placeholders."""
    with pytest.raises(NotImplementedError):
        PromptfooAdapter().run(EvalAdapterRunRequest(adapter_name="promptfoo", config={}))
    with pytest.raises(NotImplementedError):
        RagasAdapter().run(EvalAdapterRunRequest(adapter_name="ragas", config={}))
    assert "Promptfoo is planned" in (PromptfooAdapter.__doc__ or "")
    assert "Ragas is planned" in (RagasAdapter.__doc__ or "")
