"""Evaluator evidence score tests."""

from aion_brain.evaluation.evaluator import Evaluator
from tests.test_evaluator import make_trace


def test_evaluator_includes_evidence_grounding_score() -> None:
    """Evaluator scores supported grounding claims."""
    trace = make_trace().model_copy(
        update={
            "outcome": {
                "status": "planned",
                "grounding_claims": [{"verification_status": "supported"}],
            }
        }
    )

    evaluation = Evaluator().evaluate(trace)

    assert evaluation.scores["evidence_grounding_score"] == 1.0
