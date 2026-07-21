"""AION-190 runtime-boundary and script-gate tests."""

from __future__ import annotations

import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from aion_brain.contracts.memory_consolidation import (
    ConsolidationOutcome,
    EpisodicMemoryReference,
    ReplayBatch,
)
from aion_brain.memory_consolidation import ConsolidationService

ROOT = Path(__file__).resolve().parents[3]
NOW = datetime(2026, 7, 21, 17, 45, tzinfo=UTC)


def reference() -> EpisodicMemoryReference:
    return EpisodicMemoryReference(
        episode_id="episode-boundary",
        source="aion-190-boundary-test",
        content_summary="memory consolidation boundary evidence",
        occurred_at=NOW,
        salience_tags=("concept:boundary",),
        evidence_refs=("aion://aion-190/boundary/episode",),
        importance=0.7,
        confidence=0.9,
        metadata={"semantic_statement": "memory consolidation remains local"},
    )


def test_runtime_effect_flags_fail_closed() -> None:
    with pytest.raises(ValidationError):
        ReplayBatch(
            batch_id="runtime-batch",
            references=(reference(),),
            selection_reason="runtime rejected",
            max_items=1,
            runtime_effect=True,
            generated_at=NOW,
        )

    outcome = ConsolidationService().run(
        (reference(),),
        batch_id="runtime-outcome-batch",
        max_items=1,
        outcome_id="runtime-outcome",
    )
    with pytest.raises(ValidationError):
        ConsolidationOutcome(
            outcome_id="runtime-outcome-invalid",
            checkpoint=outcome.checkpoint,
            semantic_candidates=outcome.semantic_candidates,
            procedural_candidates=outcome.procedural_candidates,
            contradiction_resolutions=outcome.contradiction_resolutions,
            forgetting_candidates=outcome.forgetting_candidates,
            pipeline_stages=outcome.pipeline_stages,
            promotion_performed=True,
            created_at=NOW,
        )


def test_no_runtime_registration_or_api_route_added() -> None:
    assert not (ROOT / "services/brain-api/src/aion_brain/api/memory_consolidation.py").exists()
    kernel_files = (
        ROOT / "services/brain-api/src/aion_brain/kernel/container.py",
        ROOT / "services/brain-api/src/aion_brain/kernel/diagnostics.py",
    )
    for path in kernel_files:
        assert "aion_brain.memory_consolidation" not in path.read_text()


def test_memory_consolidation_source_avoids_prohibited_runtime_imports() -> None:
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
    source_roots = (
        ROOT / "services/brain-api/src/aion_brain/memory_consolidation",
        ROOT / "services/brain-api/src/aion_brain/contracts",
    )
    source_files = tuple(source_roots[0].glob("*.py")) + (
        ROOT / "services/brain-api/src/aion_brain/contracts/memory_consolidation.py",
    )
    for path in source_files:
        text = path.read_text()
        for marker in prohibited:
            assert marker not in text


def test_cognitive_memory_consolidation_scripts_are_executable_and_pass() -> None:
    env = {
        **os.environ,
        "PYTEST_CURRENT_TEST": "AION-190 focused script test",
    }
    scripts = (
        "scripts/cognitive-memory-consolidation-no-go-regression.sh",
        "scripts/cognitive-memory-consolidation-check.sh",
    )
    for script in scripts:
        path = ROOT / script
        assert path.is_file()
        assert os.access(path, os.X_OK)
        subprocess.run([str(path)], cwd=ROOT, env=env, check=True)


def test_memory_consolidation_imports_without_runtime_side_effects() -> None:
    subprocess.run(
        [
            sys.executable,
            "-c",
            "import aion_brain.contracts.memory_consolidation; "
            "import aion_brain.memory_consolidation",
        ],
        cwd=ROOT / "services/brain-api",
        check=True,
    )
