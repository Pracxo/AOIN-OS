"""AION-211 evidence contribution tests."""

from decimal import Decimal

from aion_brain.contracts.knowledge_epistemic_assessment import (
    EvidenceGroupDisposition,
    ScopeApplicability,
)
from aion_brain.knowledge_intelligence.epistemic_corroboration import (
    build_contribution_indexes,
    resolve_evidence_contributions,
)
from tests.test_knowledge_epistemic_assessment_helpers import (
    assessment_request,
    evidence_binding,
    source_registry_repository,
)


def test_evidence_binding_resolves_to_redacted_contribution() -> None:
    registry = source_registry_repository()
    request = assessment_request()
    contributions = resolve_evidence_contributions(
        (evidence_binding(),),
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
    assert contributions[0].disposition == EvidenceGroupDisposition.COUNTED_SUPPORT
    assert contributions[0].claim_verified is False
    assert contributions[0].knowledge_effect is False
