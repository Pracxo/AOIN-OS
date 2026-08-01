from __future__ import annotations

from copy import deepcopy

import pytest
from pydantic import ValidationError

from aion_brain.contracts import v02_release_qualification as c


def test_resource_limits_and_public_constants_are_exact():
    limits = c.resource_limits().model_dump()
    assert limits == {**c.POSITIVE_RESOURCE_LIMITS, **c.ZERO_RESOURCE_LIMITS}
    assert c.PROGRAM_ID == "AION-V02-RELEASE-QUALIFICATION-001"
    assert c.AUTHORIZATION_TRANSACTION_ID == "AION-238-V02RQ-0001"
    assert c.IMPLEMENTATION_TASK == "AION-239"
    assert c.FORMAL_CLOSEOUT_TASK == "AION-240"
    assert len(c.READINESS_DOMAINS) == 20
    assert len(c.CANONICAL_RELEASE_GATE_IDS) == 24
    assert "production_enabled" not in {item.value for item in c.V02ReleaseGateOutcome}


def test_canonical_builders_cover_all_required_contract_surfaces():
    binding = c.canonical_component_binding()
    authorization = c.canonical_authorization_envelope(binding)
    gap_matrix = c.canonical_gap_matrix()
    release_gates = c.canonical_release_gate_matrix()

    assert authorization.authorization_active is True
    assert authorization.authorization_consumed is False
    assert tuple(authorization.allowed_readiness_domains) == c.READINESS_DOMAINS
    assert len(gap_matrix.gaps) == 20
    assert gap_matrix.staging_evidence_required is True
    assert gap_matrix.production_evidence_required is True
    assert len(c.canonical_identity_provider_manifests()) == 1
    assert len(c.canonical_key_policies()) == 3
    assert len(c.canonical_protected_material_policy().classes) >= 10
    assert len(c.canonical_credential_policies()) == 4
    assert len(c.canonical_token_policies()) == 4
    assert len(c.canonical_session_policies()) == 3
    assert len(c.canonical_deployment_manifests()) == 1
    assert len(c.canonical_sbom_projection().components) >= 12
    assert len(c.canonical_provenance_records()) >= 4
    assert len(c.canonical_reproducibility_projections()) == 2
    assert len(c.canonical_rollback_plans()) == 2
    assert len(c.canonical_observability_schema().signals) >= 24
    assert len(c.canonical_health_readiness_schema().checks) >= 12
    assert len(c.canonical_threat_model().scenarios) >= 40
    assert len(release_gates.gates) == 24
    assert release_gates.v02_release_ready is False
    assert c.canonical_staging_plan().staging_deployment_enabled is False


def test_gap_matrix_rejects_duplicate_circular_and_false_resolution():
    matrix = c.canonical_gap_matrix()
    with pytest.raises(ValidationError):
        c.V02ProductionReadinessGapMatrix(
            gaps=(matrix.gaps[0], matrix.gaps[0]),
            evidence_requirements=matrix.evidence_requirements,
            readiness_domains_represented=c.READINESS_DOMAINS,
        )

    first_payload = matrix.gaps[0].model_dump()
    second_payload = matrix.gaps[1].model_dump()
    first_payload.update(
        dependency_gap_ids=(matrix.gaps[1].gap_id,),
        gap_fingerprint=None,
    )
    second_payload.update(
        dependency_gap_ids=(matrix.gaps[0].gap_id,),
        gap_fingerprint=None,
    )
    circular_gaps = (
        c.V02ProductionReadinessGap(**first_payload),
        c.V02ProductionReadinessGap(**second_payload),
        *matrix.gaps[2:],
    )
    with pytest.raises(ValidationError):
        c.V02ProductionReadinessGapMatrix(
            gaps=circular_gaps,
            evidence_requirements=matrix.evidence_requirements,
            readiness_domains_represented=c.READINESS_DOMAINS,
        )

    resolved_payload = matrix.gaps[0].model_dump()
    resolved_payload.update(
        current_status=c.V02GapStatus.resolved_by_verified_evidence,
        evidence_maturity=c.V02EvidenceMaturity.verified_local,
        current_evidence_fingerprints=(),
        staging_evidence_required=False,
        production_evidence_required=False,
        gap_fingerprint=None,
    )
    with pytest.raises(ValidationError):
        c.V02ProductionReadinessGap(**resolved_payload)

    downgraded = matrix.gaps[0].model_dump()
    downgraded.update(
        severity=c.V02GapSeverity.informational,
        minimum_severity=c.V02GapSeverity.blocker,
        gap_fingerprint=None,
    )
    with pytest.raises(ValidationError):
        c.V02ProductionReadinessGap(**downgraded)


def test_protected_values_and_live_effect_claims_fail_closed():
    with pytest.raises(ValidationError):
        c.V02QualificationEvidenceRecord(
            evidence_id="AION-239-EVIDENCE-SECRET",
            evidence_maturity=c.V02EvidenceMaturity.design_recorded,
            evidence_payload_fingerprint=c.ZERO_FINGERPRINT,
            token_value="not-retained",  # type: ignore[call-arg]
        )

    manifest = c.canonical_identity_provider_manifests()[0]
    live_manifest = manifest.model_copy(update={"connect_available": True})
    with pytest.raises(ValueError):
        from aion_brain.v02_release_qualification import (
            ControlledV02ReleaseQualificationService,
        )

        ControlledV02ReleaseQualificationService().validate_identity_provider_manifests(
            (live_manifest,)
        )

    rollback = c.canonical_rollback_plans()[0]
    changed = deepcopy(rollback.steps[0].model_dump())
    changed.update(command_present=True, step_fingerprint=None)
    command_step = c.V02RollbackStep(**changed)
    command_plan = rollback.model_copy(update={"steps": (command_step,)})
    with pytest.raises(ValueError):
        from aion_brain.v02_release_qualification import (
            ControlledV02ReleaseQualificationService,
        )

        ControlledV02ReleaseQualificationService().validate_rollback_plans(
            (command_plan,)
        )
