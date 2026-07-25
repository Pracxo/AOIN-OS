"""AION-211 concurrency tests."""

from concurrent.futures import ThreadPoolExecutor

from aion_brain.knowledge_intelligence.epistemic_assessment import stable_assessment_json
from tests.test_knowledge_epistemic_assessment_helpers import assessment_batch


def test_parallel_assessments_are_deterministic_and_in_memory() -> None:
    with ThreadPoolExecutor(max_workers=4) as executor:
        outputs = tuple(
            executor.map(lambda _item: stable_assessment_json(assessment_batch()), range(4))
        )
    assert len(set(outputs)) == 1
