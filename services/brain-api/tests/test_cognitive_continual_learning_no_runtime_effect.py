"""AION-196 runtime-boundary and script-gate tests."""

from __future__ import annotations

import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from aion_brain.contracts.continual_learning import (
    ContinualLearningObservation,
    LearningCandidate,
    LearningEpisode,
    ReplaySample,
)

ROOT = Path(__file__).resolve().parents[3]
NOW = datetime(2026, 7, 22, 4, 45, tzinfo=UTC)


def observation() -> ContinualLearningObservation:
    return ContinualLearningObservation(
        observation_id="observation-boundary",
        source="aion-196-boundary-test",
        summary="continual learning boundary evidence",
        signal_tags=("policy:boundary",),
        evidence_refs=("aion://aion-196/boundary/observation",),
        confidence=0.9,
        observed_at=NOW,
    )


def episode() -> LearningEpisode:
    return LearningEpisode(
        episode_id="episode-boundary",
        observations=(observation(),),
        outcome_label="success",
        baseline_ref="baseline://aion-196/immutable-baseline",
        policy_ref="policy://aion-196/promotion-policy",
        evidence_refs=("aion://aion-196/boundary/episode",),
        occurred_at=NOW,
    )


def replay_sample() -> ReplaySample:
    return ReplaySample(
        sample_id="replay-boundary",
        episode_ids=("episode-boundary",),
        excluded_holdout_episode_ids=("episode-holdout",),
        baseline_ref="baseline://aion-196/immutable-baseline",
        policy_ref="policy://aion-196/promotion-policy",
        max_episodes=1,
        generated_at=NOW,
    )


def test_runtime_effect_flags_fail_closed() -> None:
    with pytest.raises(ValidationError):
        ReplaySample(
            sample_id="runtime-replay",
            episode_ids=("episode-boundary",),
            baseline_ref="baseline://aion-196/immutable-baseline",
            policy_ref="policy://aion-196/promotion-policy",
            max_episodes=1,
            runtime_effect=True,
            generated_at=NOW,
        )

    with pytest.raises(ValidationError):
        LearningCandidate(
            candidate_id="runtime-candidate",
            candidate_type="memory",
            version=1,
            baseline_ref="baseline://aion-196/immutable-baseline",
            replay_sample_id="replay-boundary",
            source_episode_ids=("episode-boundary",),
            summary="runtime rejected",
            confidence=0.9,
            evidence_refs=("aion://aion-196/boundary/candidate",),
            model_weight_training=1,
            generated_at=NOW,
        )


def test_no_runtime_registration_or_api_route_added() -> None:
    assert not (ROOT / "services/brain-api/src/aion_brain/api/continual_learning.py").exists()
    for relative in (
        "services/brain-api/src/aion_brain/kernel/container.py",
        "services/brain-api/src/aion_brain/kernel/diagnostics.py",
    ):
        text = (ROOT / relative).read_text()
        assert "ExperienceReplayService" not in text
        assert "aion_brain.continual_learning" not in text


def test_continual_learning_source_avoids_prohibited_runtime_imports() -> None:
    prohibited = (
        "aion_brain.api",
        "aion_brain.git",
        "aion_brain.pull_requests",
        "aion_brain.deployment",
        "aion_brain.connectors",
        "aion_brain.model_providers",
        "aion_brain.credentials",
        "requests",
        "httpx",
        "urllib",
        "socket",
        "subprocess",
        "openai",
        "anthropic",
    )
    source_files = tuple(
        (ROOT / "services/brain-api/src/aion_brain/continual_learning").glob("*.py")
    ) + (
        ROOT / "services/brain-api/src/aion_brain/contracts/continual_learning.py",
    )
    for path in source_files:
        text = path.read_text()
        for marker in prohibited:
            assert marker not in text


def test_cognitive_continual_learning_scripts_are_executable_and_pass() -> None:
    env = {
        **os.environ,
        "PYTEST_CURRENT_TEST": "AION-196 focused script test",
    }
    scripts = (
        "scripts/cognitive-continual-learning-no-go-regression.sh",
        "scripts/cognitive-continual-learning-check.sh",
    )
    for script in scripts:
        path = ROOT / script
        assert path.is_file()
        assert os.access(path, os.X_OK)
        subprocess.run([str(path)], cwd=ROOT, env=env, check=True)


def test_continual_learning_imports_without_runtime_side_effects() -> None:
    subprocess.run(
        [
            sys.executable,
            "-c",
            "import aion_brain.contracts.continual_learning; "
            "import aion_brain.continual_learning",
        ],
        cwd=ROOT / "services/brain-api",
        check=True,
    )
