"""AION-185 persistent-state closeout and world-model authorization tests."""

from __future__ import annotations

import json
import sqlite3
import sys
from datetime import UTC, datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts/lib"))

from cognitive_architecture_governance import (  # noqa: E402
    AION183_AUTHORIZATION_ID,
    AION185_AUTHORIZATION_ID,
    AION185_EVALUATION_ID,
    AION186_SCOPE,
    AION186_TASK_ID,
    AION187_AUTHORIZATION_ID,
    AION189_AUTHORIZATION_ID,
    AION191_AUTHORIZATION_ID,
    AION193_AUTHORIZATION_ID,
    PROGRAM_ID,
    validate_aion185_authorization_payload,
    validate_aion185_evaluation_payload,
    validate_persistent_state_closeout,
    validate_persistent_state_closeout_no_go,
)

from aion_brain.cognitive_architecture.repository import (  # noqa: E402
    ExplicitLocalCognitiveStateRepository,
    StaleCognitiveStateVersionError,
)
from aion_brain.cognitive_architecture.state import (  # noqa: E402
    CognitiveStateService,
    ContradictionDetector,
    UncertaintyTracker,
)
from aion_brain.contracts.cognitive_state import (  # noqa: E402
    BeliefRecord,
    CognitiveEvent,
    CognitiveStateCheckpoint,
    CognitiveStateProvenance,
)

NOW = datetime(2026, 7, 21, 8, 30, tzinfo=UTC)

REQUIRED_FILES = (
    "docs/cognitive-architecture/tasks/AION-185.md",
    "docs/cognitive-architecture/program-ledger.json",
    "docs/cognitive-architecture/authorization-ledger.json",
    "examples/cognitive-architecture/aion-185-persistent-state-evaluation.json",
    "examples/cognitive-architecture/aion-185-world-model-authorization.json",
    "scripts/cognitive-persistent-state-closeout-check.sh",
    "scripts/cognitive-persistent-state-closeout-no-go-regression.sh",
    "scripts/lib/cognitive_architecture_governance.py",
)


def _json(relative: str) -> dict:
    return json.loads((ROOT / relative).read_text())


def _provenance(operation_id: str) -> CognitiveStateProvenance:
    return CognitiveStateProvenance(
        provenance_id=f"prov-{operation_id}",
        operation_id=operation_id,
        actor_id="operator",
        source="aion-185-synthetic-evaluation",
        evidence_refs=("aion://evidence/aion-185",),
        created_at=NOW,
    )


def _belief_payload(belief_id: str, statement: str, confidence: float = 0.8) -> dict:
    return BeliefRecord(
        belief_id=belief_id,
        statement=statement,
        confidence=confidence,
        source_refs=("aion://evidence/aion-185-belief",),
        revision_sequence=1,
        created_at=NOW,
        updated_at=NOW,
    ).model_dump(mode="json")


def _event(
    *,
    event_id: str,
    idempotency_key: str,
    expected_previous_sequence: int,
    payload: dict,
    event_type: str = "belief_recorded",
) -> CognitiveEvent:
    return CognitiveEvent(
        event_id=event_id,
        idempotency_key=idempotency_key,
        event_type=event_type,
        expected_previous_sequence=expected_previous_sequence,
        payload=payload,
        provenance=_provenance(event_id),
        created_at=NOW,
    )


def test_aion_185_required_files_exist() -> None:
    for relative in REQUIRED_FILES:
        assert (ROOT / relative).is_file(), relative


def test_aion_185_ledgers_examples_and_no_go_validate() -> None:
    validate_persistent_state_closeout(ROOT)
    validate_persistent_state_closeout_no_go(ROOT)

    evaluation = _json("examples/cognitive-architecture/aion-185-persistent-state-evaluation.json")
    authorization = _json("examples/cognitive-architecture/aion-185-world-model-authorization.json")
    validate_aion185_evaluation_payload(evaluation)
    validate_aion185_authorization_payload(authorization)

    program = _json("docs/cognitive-architecture/program-ledger.json")
    auth_ledger = _json("docs/cognitive-architecture/authorization-ledger.json")

    assert program["program_id"] == PROGRAM_ID
    assert program["active_cognitive_implementation_authorization"] in {
        AION185_AUTHORIZATION_ID,
        AION187_AUTHORIZATION_ID,
        AION189_AUTHORIZATION_ID,
        AION191_AUTHORIZATION_ID,
        AION193_AUTHORIZATION_ID,
    }
    assert auth_ledger["active_cognitive_implementation_authorization"] in {
        AION185_AUTHORIZATION_ID,
        AION187_AUTHORIZATION_ID,
        AION189_AUTHORIZATION_ID,
        AION191_AUTHORIZATION_ID,
        AION193_AUTHORIZATION_ID,
    }
    assert auth_ledger["active_cognitive_implementation_authorization_count"] == 1

    closed = auth_ledger["records"][0]
    world_model = next(
        item
        for item in auth_ledger["records"]
        if item["authorization_id"] == AION185_AUTHORIZATION_ID
    )
    assert closed["authorization_id"] == AION183_AUTHORIZATION_ID
    assert closed["authorization_active"] is False
    assert closed["authorization_consumed"] is True
    assert closed["authorization_closeout_evaluation"] == AION185_EVALUATION_ID
    assert world_model["authorization_id"] == AION185_AUTHORIZATION_ID
    assert world_model["implementation_task"] == AION186_TASK_ID
    if world_model["record_kind"] == "implementation_authorization":
        assert world_model["scope"] == AION186_SCOPE


def test_aion_185_evaluation_scenario_preserves_replay_and_restart(tmp_path: Path) -> None:
    database = tmp_path / "aion-185-state.sqlite"
    repository = ExplicitLocalCognitiveStateRepository(database_path=database, initialize=True)
    service = CognitiveStateService(repository=repository)

    first = _event(
        event_id="event-route-clear",
        idempotency_key="idem-route-clear",
        expected_previous_sequence=0,
        payload=_belief_payload("belief-route-clear", "route: clear"),
    )
    second = _event(
        event_id="event-route-blocked",
        idempotency_key="idem-route-blocked",
        expected_previous_sequence=1,
        payload=_belief_payload("belief-route-blocked", "route: blocked", 0.9),
    )
    service.record_event(first)
    service.record_event(second)

    duplicate = service.record_event(first)
    assert duplicate.duplicate is True
    assert service.current_snapshot().sequence == 2

    with pytest.raises(StaleCognitiveStateVersionError):
        service.record_event(
            _event(
                event_id="event-stale",
                idempotency_key="idem-stale",
                expected_previous_sequence=0,
                payload=_belief_payload("belief-stale", "route: stale"),
            )
        )

    contradictions = ContradictionDetector().detect(service.current_snapshot())
    assert len(contradictions) == 1
    service.record_event(
        _event(
            event_id="event-contradiction",
            idempotency_key="idem-contradiction",
            expected_previous_sequence=2,
            event_type="contradiction_recorded",
            payload=contradictions[0].model_dump(mode="json"),
        )
    )
    uncertainty = UncertaintyTracker().build_uncertainty_event(
        subject="route",
        uncertainty_score=0.7,
        previous_score=0.2,
        rationale="conflicting synthetic local evidence",
        provenance=_provenance("uncertainty"),
        expected_previous_sequence=3,
        idempotency_key="idem-uncertainty",
        uncertainty_id="uncertainty-route",
    )
    service.record_event(uncertainty)

    checkpoint = service.create_checkpoint(
        checkpoint_id="checkpoint-aion-185",
        provenance=_provenance("checkpoint"),
    )
    retained = service.apply_retention(
        retain_from_sequence=2,
        provenance=_provenance("retention"),
        idempotency_key="idem-retention",
    ).snapshot

    restarted = CognitiveStateService(
        repository=ExplicitLocalCognitiveStateRepository(database_path=database)
    )
    replayed = restarted.current_snapshot()

    assert replayed.content_hash == retained.content_hash
    assert replayed.sequence == retained.sequence
    assert replayed.retained_from_sequence == 2
    assert checkpoint.snapshot_hash == checkpoint.snapshot.content_hash

    with sqlite3.connect(database) as connection:
        row_count = connection.execute("SELECT COUNT(*) FROM cognitive_state_events").fetchone()[0]
    assert row_count == 4

    with pytest.raises(ValidationError):
        CognitiveStateCheckpoint(
            checkpoint_id="bad-checkpoint",
            sequence=checkpoint.sequence,
            snapshot=checkpoint.snapshot,
            snapshot_hash="0" * 64,
            provenance=_provenance("bad-checkpoint"),
        )


def test_aion_185_adds_no_world_model_runtime_surface() -> None:
    program = _json("docs/cognitive-architecture/program-ledger.json")
    aion_186_implemented = any(
        record.get("implementation_task") == "AION-186"
        and record.get("task_state")
        in {
            "implemented_pending_aion_187_evaluation",
            "merged_evaluated_passed",
        }
        for record in program["records"]
    )
    assert aion_186_implemented or not (
        ROOT / "services/brain-api/src/aion_brain/world_model"
    ).exists()
    assert aion_186_implemented or not (
        ROOT / "services/brain-api/src/aion_brain/contracts/world_model.py"
    ).exists()
    assert not (ROOT / "services/brain-api/src/aion_brain/api/world_model.py").exists()
