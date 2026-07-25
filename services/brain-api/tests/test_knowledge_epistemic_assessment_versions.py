"""AION-211 version scope tests."""

from decimal import Decimal

from aion_brain.contracts.knowledge_epistemic_assessment import (
    EpistemicTargetScope,
    epistemic_target_scope_fingerprint,
)
from aion_brain.knowledge_intelligence.epistemic_assessment import evaluate_version_applicability
from tests.test_knowledge_claim_graph_helpers import claim, valid_interval, version


def test_version_mismatch_is_not_applicable() -> None:
    payload = {
        "target_valid_time": valid_interval(),
        "target_jurisdiction_ids": ("global",),
        "target_version_scopes": (version("different-target", "2.0"),),
    }
    target = EpistemicTargetScope(
        **payload,
        scope_fingerprint=epistemic_target_scope_fingerprint(payload),
    )
    applicability, factor = evaluate_version_applicability(claim(), target)
    assert applicability == "not_applicable"
    assert factor == Decimal("0.000000")
