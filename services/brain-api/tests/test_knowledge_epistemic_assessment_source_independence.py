"""AION-211 source-independence tests."""

from decimal import Decimal

from aion_brain.contracts.knowledge_claim_graph import EvidenceRole
from aion_brain.contracts.knowledge_epistemic_assessment import ScopeApplicability
from aion_brain.knowledge_intelligence.epistemic_corroboration import (
    build_contribution_indexes,
    resolve_evidence_contributions,
    score_role,
)
from tests.test_knowledge_epistemic_assessment_helpers import (
    assessment_request,
    evidence_binding,
    source_registry_repository,
)


def test_source_independence_counts_unique_groups() -> None:
    registry = source_registry_repository(additional_group_ids=("independence-group-0002",))
    request = assessment_request()
    contributions = resolve_evidence_contributions(
        (
            evidence_binding(binding_id="binding-0001"),
            evidence_binding(
                binding_id="binding-0002",
                group_id="independence-group-0002",
                lineage_record_id="source-registry-source-lineage-0005",
                evidence_role=EvidenceRole.SUPPORTS,
            ),
        ),
        indexes=build_contribution_indexes(registry.records()),
        claim_scope_factors=(
            ScopeApplicability.APPLICABLE,
            Decimal("1.000000"),
            ScopeApplicability.APPLICABLE,
            Decimal("1.000000"),
            ScopeApplicability.APPLICABLE,
            Decimal("1.000000"),
        ),
        freshness_policy=request.freshness_policy,
        assessment_time=request.assessment_time,
    )
    score = score_role(claim_id="claim-0001", role="support", contributions=contributions)
    assert score.independent_group_count == 2
    assert score.source_independence == Decimal("1.000000")
