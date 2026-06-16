from __future__ import annotations

from datetime import UTC, datetime, timedelta

from aion_brain.contracts.beliefs import TruthMaintenanceRequest
from tests.belief_helpers import belief_bundle, create_claim


def test_truth_maintenance_dry_run_does_not_revise_claim() -> None:
    bundle = belief_bundle()
    claim = create_claim(bundle, "A dry run can inspect a claim.", confidence=0.4)

    run = bundle.truth.run(
        TruthMaintenanceRequest(owner_scope=["workspace:main"], claim_ids=[claim.claim_id])
    )

    stored = bundle.repository.get_claim(claim.claim_id)
    assert run.status == "dry_run"
    assert run.revised_claim_ids == []
    assert stored is not None
    assert stored.confidence == 0.4


def test_truth_maintenance_marks_old_claim_stale_when_not_dry_run() -> None:
    bundle = belief_bundle()
    claim = create_claim(bundle, "An old claim can become stale.", confidence=0.7)
    bundle.repository.save_claim(
        claim.model_copy(update={"observed_at": datetime.now(UTC) - timedelta(days=365)})
    )

    run = bundle.truth.run(
        TruthMaintenanceRequest(
            owner_scope=["workspace:main"],
            claim_ids=[claim.claim_id],
            dry_run=False,
        )
    )

    updated = bundle.repository.get_claim(claim.claim_id)
    assert run.status == "completed"
    assert claim.claim_id in run.stale_claim_ids
    assert claim.claim_id in run.revised_claim_ids
    assert updated is not None
    assert updated.status == "stale"


def test_truth_maintenance_marks_high_contradiction_contradicted() -> None:
    bundle = belief_bundle()
    claim = create_claim(bundle, "A contradicted claim should be revised.", confidence=0.8)
    contradiction = bundle.contradictions.create_contradiction(
        claim_id=claim.claim_id,
        source_type="generic",
        source_id="source-conflict",
        severity="high",
        reason="conflict",
    )

    run = bundle.truth.run(
        TruthMaintenanceRequest(
            owner_scope=["workspace:main"],
            claim_ids=[claim.claim_id],
            dry_run=False,
        )
    )

    updated = bundle.repository.get_claim(claim.claim_id)
    assert contradiction.contradiction_id in run.contradiction_ids
    assert updated is not None
    assert updated.status == "contradicted"
