"""AION-211 jurisdiction scope tests."""

from decimal import Decimal

from aion_brain.contracts.knowledge_claim_graph import JurisdictionKind
from aion_brain.contracts.knowledge_epistemic_assessment import (
    EpistemicTargetScope,
    epistemic_target_scope_fingerprint,
)
from aion_brain.knowledge_intelligence.epistemic_assessment import (
    evaluate_jurisdiction_applicability,
)
from tests.test_knowledge_claim_graph_helpers import (
    claim,
    jurisdiction,
    scope,
    valid_interval,
    version,
)


def test_jurisdiction_mismatch_is_not_applicable() -> None:
    scoped_claim = claim(
        claim_scope=scope(
            jurisdictions=(jurisdiction("us", JurisdictionKind.COUNTRY),),
        )
    )
    payload = {
        "target_valid_time": valid_interval(),
        "target_jurisdiction_ids": ("eu",),
        "target_version_scopes": (version(),),
    }
    target = EpistemicTargetScope(
        **payload,
        scope_fingerprint=epistemic_target_scope_fingerprint(payload),
    )
    applicability, factor = evaluate_jurisdiction_applicability(scoped_claim, target)
    assert applicability == "not_applicable"
    assert factor == Decimal("0.000000")
