from __future__ import annotations

import pytest
from governed_engagement_learning_test_helpers import (
    SHADOW_SESSION_ID,
    build_synthetic_shadow_pilot_inputs,
)

from aion_brain.contracts.governed_engagement_learning import (
    EngagementApplicationQuery,
    EngagementApplicationStatus,
    EngagementCounterfactualRecommendation,
    EngagementOverlayRecord,
    EngagementOverlayStatus,
    build_record,
)
from aion_brain.governed_learning_memory.engagement_overlay import (
    InMemoryEngagementOverlayRepository,
)


def _run_pilot():
    inputs = build_synthetic_shadow_pilot_inputs()
    return (
        inputs,
        *inputs.service.run_application(
            shadow_session_id=SHADOW_SESSION_ID,
            signal_batch=inputs.signal_batch,
            candidates=inputs.candidates,
            approval_records=inputs.approval_records,
            fixture_fingerprint=inputs.fixture_fingerprint,
            operator_identity_fingerprint=inputs.operator_identity_fingerprint,
            expires_at=inputs.expires_at,
            now=inputs.now,
        ),
    )


def test_shadow_application_runs_in_memory_and_returns_zero_effect_result():
    _inputs, plan, result = _run_pilot()

    assert len(plan.candidate_bindings) == 9
    assert len(plan.approval_bundles) == 9
    assert len(plan.adaptation_identities) == 9
    assert plan.overlay_snapshot.record_count == 9
    assert len(plan.counterfactual_cases) == 9
    assert len(result.counterfactual_results) == 9
    assert result.status is EngagementApplicationStatus.SHADOW_APPLIED
    assert result.recommendation is EngagementCounterfactualRecommendation.APPROVE_SHADOW_CANDIDATE
    assert result.overlay_expired_or_rolled_back is True
    assert result.active_overlay_records_after_close == 0
    assert result.persistent_engagement_overlay_writes == 0
    assert result.aion_224_store_writes == 0
    assert result.production_policy_mutations == 0
    assert result.engagement_confidence_effects == 0
    assert result.engagement_knowledge_effects == 0
    assert result.cognitive_memory_writes == 0
    assert result.actual_belief_creations == 0
    assert result.actual_belief_mutations == 0
    assert result.model_weight_changes == 0
    assert result.runtime_effect is False


def test_overlay_repository_is_copy_on_write_queryable_and_rejects_changed_replay():
    _inputs, plan, _result = _run_pilot()
    repo = InMemoryEngagementOverlayRepository().with_overlays(
        plan.overlay_snapshot.records
    ).with_snapshot(plan.overlay_snapshot)
    repeat = repo.with_overlays(plan.overlay_snapshot.records).with_snapshot(
        plan.overlay_snapshot
    )

    assert repeat.audit() == {
        "overlay_count": 9,
        "snapshot_count": 1,
        "persistent_overlay_writes": 0,
        "production_policy_mutations": 0,
    }
    query = build_record(
        EngagementApplicationQuery,
        {
            "schema_version": "aion-glm-engagement-application-query/v1",
            "query_id": "query-shadow-session",
            "shadow_session_id": SHADOW_SESSION_ID,
            "overlay_status": EngagementOverlayStatus.ACTIVE_SHADOW,
            "limit": 100,
            "runtime_effect": False,
        },
        "query_fingerprint",
    )
    result = repeat.query(query)
    assert result.result_count == 9
    assert {record.status for record in result.overlay_records} == {
        EngagementOverlayStatus.ACTIVE_SHADOW
    }

    original = plan.overlay_snapshot.records[0]
    payload = original.model_dump(mode="python", exclude={"overlay_fingerprint"})
    payload["target_policy"] = original.target_policy
    changed = build_record(
        EngagementOverlayRecord,
        {
            **payload,
            "reason_codes": (
                *original.reason_codes,
                "engagement_overlay_expired",
            ),
        },
        "overlay_fingerprint",
    )
    with pytest.raises(ValueError):
        repeat.with_overlay(changed)


def test_overlay_expiry_and_rollback_leave_no_active_shadow_records():
    _inputs, plan, _result = _run_pilot()
    repo = InMemoryEngagementOverlayRepository().with_overlays(plan.overlay_snapshot.records)

    expired = repo.expire_session(SHADOW_SESSION_ID)
    rolled_back = repo.rollback_session(SHADOW_SESSION_ID)

    assert expired.active_overlay_count() == 0
    assert rolled_back.active_overlay_count() == 0
    assert {item.status for item in expired.overlays_by_candidate(
        plan.overlay_snapshot.records[0].candidate_id
    )} == {EngagementOverlayStatus.EXPIRED}
    assert {item.status for item in rolled_back.overlays_by_candidate(
        plan.overlay_snapshot.records[0].candidate_id
    )} == {EngagementOverlayStatus.ROLLED_BACK}
