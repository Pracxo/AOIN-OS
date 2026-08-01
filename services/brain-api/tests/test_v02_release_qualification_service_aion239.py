from __future__ import annotations

import pytest

from aion_brain.contracts import v02_release_qualification as c
from aion_brain.v02_release_qualification import (
    ControlledV02ReleaseQualificationService,
)


def test_controlled_service_runs_one_disabled_pilot_with_release_hold():
    result = ControlledV02ReleaseQualificationService().run_canonical_disabled_pilot()

    assert result.pilot_id == c.PILOT_ID
    assert result.authorization_id == c.AUTHORIZATION_TRANSACTION_ID
    assert result.qualification_sessions_started == 1
    assert result.qualification_sessions_closed == 1
    assert result.active_qualification_sessions_after_close == 0
    assert result.readiness_domains_evaluated == 20
    assert result.readiness_gaps_evaluated == 20
    assert result.identity_provider_manifests_validated == 1
    assert result.public_key_lifecycle_policies_validated == 3
    assert result.protected_material_classes_validated >= 10
    assert result.credential_lifecycle_policies_validated == 4
    assert result.token_lifecycle_policies_validated == 4
    assert result.session_lifecycle_policies_validated == 3
    assert result.replay_provisioning_plans_validated == 1
    assert result.deployment_artifact_manifests_validated == 1
    assert result.sbom_components_projected >= 12
    assert result.artifact_provenance_records_validated >= 4
    assert result.reproducibility_projections_validated == 2
    assert result.rollback_plans_validated == 2
    assert result.rollback_drill_plans_validated == 1
    assert result.rollback_drill_simulations == 1
    assert result.observability_signals_validated >= 24
    assert result.health_readiness_checks_validated >= 12
    assert result.threat_scenarios_validated >= 40
    assert result.release_gates_evaluated == 24
    assert result.staging_qualification_plans_validated == 1
    assert result.exact_replays_returned == 1
    assert result.changed_replays_rejected == 1
    assert result.release_ready_decisions == 0
    assert result.release_hold_decisions == 1
    assert result.v02_release_ready is False
    assert result.v02_release_candidate_created is False
    assert result.integrity_passed is True
    assert sum(result.prohibited_effect_counters.values()) == 0


def test_repository_exact_replay_is_idempotent_and_changed_replay_rejected():
    service = ControlledV02ReleaseQualificationService()
    result = service.run_canonical_disabled_pilot()
    request = service.repository._run_request_fingerprints[result.run_id]

    replayed = service.replay_exact_run(result.run_id, request)
    assert replayed.report_fingerprint == result.report_fingerprint

    changed = c.v02_qualification_fingerprint({"run_id": result.run_id, "changed": True})
    with pytest.raises(ValueError):
        service.replay_exact_run(result.run_id, changed)


def test_runtime_guard_never_allows_release_or_staging_activation():
    service = ControlledV02ReleaseQualificationService()
    gap_matrix = c.canonical_gap_matrix()
    release_gates = c.canonical_release_gate_matrix()
    guard = service.evaluate_runtime_guard(
        gap_matrix=gap_matrix,
        release_gate_matrix=release_gates,
    )

    assert guard.outcome is c.V02RuntimeGuardOutcome.allow_disabled_qualification
    assert guard.release_hold is True
    assert guard.staging_evidence_required is True
    assert guard.production_evidence_required is True
    assert guard.v02_release_ready is False
    assert guard.v02_release_candidate_created is False


def test_authorization_session_and_repository_fail_closed():
    service = ControlledV02ReleaseQualificationService()
    binding = c.canonical_component_binding()
    first = service.create_session_plan("aion-239-session-one")
    second = service.create_session_plan("aion-239-session-two")
    authorization = c.canonical_authorization_envelope(binding, first.session_id)

    assert service.validate_authorization(authorization).authorization_active is True
    service.start_session(first)
    with pytest.raises(ValueError):
        service.start_session(second)
    closed = service.close_session(first.session_id)
    assert closed.active is False
    assert closed.candidate_references_loaded is False
    assert closed.evidence_references_loaded is False
