"""AION-211 fixture replay tests."""

from pathlib import Path

from aion_brain.knowledge_intelligence.epistemic_assessment import (
    ControlledEpistemicAssessmentEngine,
)
from tests.test_knowledge_claim_graph_helpers import NOW
from tests.test_knowledge_epistemic_assessment_helpers import fixture_json


def test_fixture_replay_is_local_and_in_memory(tmp_path: Path) -> None:
    path = fixture_json(tmp_path / "epistemic-fixture.json")
    batch = ControlledEpistemicAssessmentEngine(clock=lambda: NOW).replay_fixture(
        path,
        repository_root=Path.cwd().parents[1],
    )
    assert batch.assessment_count == 1
    assert batch.runtime_effect is False
