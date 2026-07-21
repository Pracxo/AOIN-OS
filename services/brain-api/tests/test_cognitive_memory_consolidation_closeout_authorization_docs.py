"""AION-191 memory-consolidation closeout and planning authorization tests."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

from aion_brain.contracts.memory_consolidation import EpisodicMemoryReference
from aion_brain.memory_consolidation import REQUIRED_PIPELINE, ConsolidationService

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts/lib"))

from cognitive_architecture_governance import (  # noqa: E402
    AION189_AUTHORIZATION_ID,
    AION190_MERGE_COMMIT,
    AION190_PR,
    AION190_TASK_ID,
    AION191_AUTHORIZATION_ID,
    AION191_EVALUATION_ID,
    AION192_SCOPE,
    AION192_TASK_ID,
    PROGRAM_ID,
    validate_aion191_authorization_payload,
    validate_aion191_evaluation_payload,
    validate_memory_consolidation_closeout,
    validate_memory_consolidation_closeout_no_go,
)

NOW = datetime(2026, 7, 21, 18, 45, tzinfo=UTC)

REQUIRED_FILES = (
    "docs/cognitive-architecture/tasks/AION-191.md",
    "docs/cognitive-architecture/program-ledger.json",
    "docs/cognitive-architecture/authorization-ledger.json",
    "examples/cognitive-architecture/aion-191-memory-consolidation-evaluation.json",
    "examples/cognitive-architecture/aion-191-planning-authorization.json",
    "scripts/cognitive-memory-consolidation-closeout-check.sh",
    "scripts/cognitive-memory-consolidation-closeout-no-go-regression.sh",
    "scripts/lib/cognitive_architecture_governance.py",
)


def _json(relative: str) -> dict:
    return json.loads((ROOT / relative).read_text())


def episode(
    episode_id: str,
    summary: str,
    *,
    concept: str = "release gate",
    statement: str | None = None,
    tags: tuple[str, ...] = (),
    importance: float = 0.5,
    confidence: float = 0.8,
    safety_critical: bool = False,
    retention_required: bool = False,
    step: str | None = None,
    step_index: int = 0,
    outcome: str = "success",
    policy_evidence_ref: str | None = None,
) -> EpisodicMemoryReference:
    metadata: dict[str, object] = {
        "semantic_statement": statement or summary,
        "outcome": outcome,
    }
    if step is not None:
        metadata["step"] = step
        metadata["step_index"] = step_index
    if policy_evidence_ref is not None:
        metadata["policy_evidence_ref"] = policy_evidence_ref
    return EpisodicMemoryReference(
        episode_id=episode_id,
        source="aion-191-evaluation-fixture",
        content_summary=summary,
        occurred_at=NOW + timedelta(minutes=step_index),
        salience_tags=(f"concept:{concept}", *tags),
        evidence_refs=(f"aion://aion-191/episode/{episode_id}",),
        importance=importance,
        confidence=confidence,
        safety_critical=safety_critical,
        retention_required=retention_required,
        metadata=metadata,
    )


def replay_fixtures() -> tuple[EpisodicMemoryReference, ...]:
    return (
        episode(
            "episode-safe-retention",
            "critical release hold retained",
            statement="release gate remains disabled until review",
            importance=1.0,
            confidence=0.96,
            safety_critical=True,
            retention_required=True,
            tags=("procedure:release-check",),
            step="verify runtime hold",
            step_index=1,
        ),
        episode(
            "episode-green-release",
            "green release gate evidence",
            statement="release gate passes when checks are green",
            importance=0.8,
            confidence=0.9,
            tags=("procedure:release-check",),
            step="collect green check evidence",
            step_index=2,
        ),
        episode(
            "episode-pending-release",
            "pending release gate evidence",
            statement="release gate waits when checks are pending",
            importance=0.7,
            confidence=0.82,
            tags=("procedure:release-check",),
            step="hold merge while checks are pending",
            step_index=3,
            outcome="failure",
        ),
        episode(
            "episode-duplicate-primary",
            "duplicate replay marker",
            concept="duplicate replay",
            statement="duplicate replay marker can be compacted",
            importance=0.6,
            confidence=0.8,
        ),
        episode(
            "episode-duplicate-secondary",
            "duplicate replay marker",
            concept="duplicate replay",
            statement="duplicate replay marker can be compacted",
            importance=0.4,
            confidence=0.75,
            policy_evidence_ref="aion://aion-191/policy/duplicate-retention",
        ),
    )


def _evaluation_outcome():
    return ConsolidationService().run(
        replay_fixtures(),
        batch_id="aion-191-evaluation",
        max_items=5,
        outcome_id="aion-191-outcome",
    )


def _evaluation_metrics() -> dict[str, float | int]:
    first = _evaluation_outcome()
    second = ConsolidationService().run(
        reversed(replay_fixtures()),
        batch_id="aion-191-evaluation",
        max_items=5,
        outcome_id="aion-191-outcome",
    )
    evidence = first.checkpoint.evidence
    deterministic = (
        first.checkpoint.replay_batch.replay_hash == second.checkpoint.replay_batch.replay_hash
    )
    forbidden_side_effects = any(
        (
            first.runtime_effect,
            first.checkpoint.runtime_effect,
            first.checkpoint.replay_batch.runtime_effect,
            first.promotion_performed,
            first.source_rewrite_performed,
            first.hidden_mutation_performed,
            first.deletion_performed,
            any(candidate.runtime_effect for candidate in first.checkpoint.candidates),
            any(candidate.approved_for_promotion for candidate in first.checkpoint.candidates),
            any(candidate.promotion_allowed for candidate in first.checkpoint.candidates),
            any(candidate.deletion_allowed for candidate in first.forgetting_candidates),
        )
    )
    return {
        "retained_critical_memories_rate": evidence.retained_critical_memories_rate,
        "duplicate_reduction_rate": evidence.duplicate_reduction_rate,
        "contradiction_loss_rate": evidence.contradiction_loss_rate,
        "catastrophic_forgetting_rate": evidence.catastrophic_forgetting_rate,
        "provenance_coverage": evidence.provenance_coverage,
        "unauthorized_promotion_count": evidence.unauthorized_promotion_count,
        "deterministic_replay_rate": 1.0 if deterministic else 0.0,
        "forbidden_side_effects": 1 if forbidden_side_effects else 0,
    }


def test_aion_191_required_files_exist() -> None:
    for relative in REQUIRED_FILES:
        path = ROOT / relative
        assert path.exists(), f"missing {relative}"
        if relative.startswith("scripts/"):
            assert os.access(path, os.X_OK), f"not executable: {relative}"


def test_aion_191_ledgers_examples_and_no_go_validate() -> None:
    validate_memory_consolidation_closeout(ROOT)
    validate_memory_consolidation_closeout_no_go(ROOT)
    validate_aion191_evaluation_payload(
        _json("examples/cognitive-architecture/aion-191-memory-consolidation-evaluation.json")
    )
    validate_aion191_authorization_payload(
        _json("examples/cognitive-architecture/aion-191-planning-authorization.json")
    )

    program = _json("docs/cognitive-architecture/program-ledger.json")
    authorization = _json("docs/cognitive-architecture/authorization-ledger.json")

    assert program["program_id"] == PROGRAM_ID
    assert program["active_cognitive_implementation_authorization"] == AION191_AUTHORIZATION_ID
    assert (
        authorization["active_cognitive_implementation_authorization"] == AION191_AUTHORIZATION_ID
    )
    assert authorization["active_cognitive_implementation_authorization_count"] == 1

    implementation = next(
        item for item in program["records"] if item.get("implementation_task") == AION190_TASK_ID
    )
    assert implementation["pr"] == AION190_PR
    assert implementation["merge_commit"] == AION190_MERGE_COMMIT
    assert implementation["task_state"] == "merged_evaluated_passed"

    closed = next(
        item
        for item in authorization["records"]
        if item["authorization_id"] == AION189_AUTHORIZATION_ID
    )
    assert closed["authorization_active"] is False
    assert closed["authorization_consumed"] is True
    assert closed["authorization_expired"] is True
    assert closed["authorization_reusable"] is False
    assert closed["authorization_closeout_evaluation"] == AION191_EVALUATION_ID
    assert closed["implementation_pr"] == AION190_PR
    assert closed["implementation_merge_commit"] == AION190_MERGE_COMMIT

    active = next(
        item
        for item in authorization["records"]
        if item["authorization_id"] == AION191_AUTHORIZATION_ID
    )
    assert active["authorization_active"] is True
    assert active["implementation_task"] == AION192_TASK_ID
    assert active["scope"] == AION192_SCOPE


def test_aion_191_memory_consolidation_evaluation_meets_thresholds() -> None:
    payload = _json("examples/cognitive-architecture/aion-191-memory-consolidation-evaluation.json")
    metrics = _evaluation_metrics()

    assert metrics == payload["hard_pass_conditions"]
    assert set(payload["evaluation_matrix"].values()) == {"PASS"}

    outcome = _evaluation_outcome()
    assert outcome.pipeline_stages == REQUIRED_PIPELINE
    assert len(outcome.semantic_candidates) >= 3
    assert outcome.procedural_candidates
    assert outcome.contradiction_resolutions
    assert outcome.forgetting_candidates
    assert outcome.checkpoint.operator_review_required is True
    assert outcome.checkpoint.promotion_status == "operator_review_required"
    assert all(candidate.evidence_refs for candidate in outcome.checkpoint.candidates)
    assert all(not candidate.promotion_allowed for candidate in outcome.checkpoint.candidates)
    assert all(not candidate.approved_for_promotion for candidate in outcome.checkpoint.candidates)
    assert all(
        candidate.explicit_policy_evidence_refs and not candidate.deletion_allowed
        for candidate in outcome.forgetting_candidates
    )
    assert outcome.promotion_performed is False
    assert outcome.source_rewrite_performed is False
    assert outcome.hidden_mutation_performed is False
    assert outcome.deletion_performed is False


def test_aion_191_does_not_implement_aion_192_runtime_surface() -> None:
    program = _json("docs/cognitive-architecture/program-ledger.json")
    planning_record = next(
        (
            item
            for item in program["records"]
            if item.get("implementation_task") == AION192_TASK_ID
        ),
        None,
    )
    planning_state = planning_record["task_state"] if planning_record else ""
    contract = ROOT / "services/brain-api/src/aion_brain/contracts/planning.py"
    source = ROOT / "services/brain-api/src/aion_brain/planning"
    contract_text = contract.read_text() if contract.exists() else ""
    source_text = (
        "\n".join(path.read_text() for path in source.glob("*.py")) if source.is_dir() else ""
    )
    if not planning_record or planning_state.startswith("implementation_pending"):
        assert "class StrategicGoal" not in contract_text
        assert "class HierarchicalPlan" not in contract_text
        assert "class StrategicPlanner" not in source_text
        assert "class ReplanningService" not in source_text
    else:
        assert planning_state == "implemented_pending_aion_193_evaluation"
    assert not (ROOT / "services/brain-api/src/aion_brain/api/planning.py").exists()


def test_aion_191_scripts_are_executable_and_pass() -> None:
    env = {
        **os.environ,
        "PYTEST_CURRENT_TEST": "AION-191 focused script test",
    }
    scripts = (
        "scripts/cognitive-memory-consolidation-closeout-no-go-regression.sh",
        "scripts/cognitive-memory-consolidation-closeout-check.sh",
    )
    for script in scripts:
        path = ROOT / script
        assert path.is_file()
        assert os.access(path, os.X_OK)
        subprocess.run([str(path)], cwd=ROOT, env=env, check=True)
