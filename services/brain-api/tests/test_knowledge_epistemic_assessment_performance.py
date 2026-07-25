"""AION-211 performance smoke tests."""

from time import perf_counter

from tests.test_knowledge_epistemic_assessment_helpers import assessment_batch


def test_small_assessment_performance_smoke() -> None:
    started = perf_counter()
    batch = assessment_batch()
    elapsed = perf_counter() - started
    assert batch.assessment_count == 1
    assert elapsed < 1.0
