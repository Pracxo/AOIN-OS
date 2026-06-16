from __future__ import annotations

from aion_brain.contracts.learning_synthesis import PatternMiningRequest
from tests.learning_synthesis_helpers import bundle, create_experience_request


def test_pattern_miner_detects_repeated_generic_pattern() -> None:
    items = bundle()
    first = items.experiences.create_experience(create_experience_request("source-1"))
    second = items.experiences.create_experience(create_experience_request("source-2"))

    run = items.miner.mine(
        PatternMiningRequest(
            owner_scope=["workspace:main"],
            experience_ids=[first.experience_id, second.experience_id],
            min_frequency=2,
            min_confidence=0.5,
            dry_run=False,
        )
    )

    assert run.status == "completed"
    assert len(run.patterns) == 1
    assert run.patterns[0].pattern_type == "repeated_failure"
    assert items.repository.list_patterns(["workspace:main"])[0].pattern_id


def test_pattern_miner_dry_run_does_not_persist_patterns() -> None:
    items = bundle()
    first = items.experiences.create_experience(create_experience_request("source-1"))
    second = items.experiences.create_experience(create_experience_request("source-2"))

    run = items.miner.mine(
        PatternMiningRequest(
            owner_scope=["workspace:main"],
            experience_ids=[first.experience_id, second.experience_id],
            dry_run=True,
        )
    )

    assert run.status == "dry_run"
    assert run.patterns
    assert items.repository.list_patterns(["workspace:main"]) == []
