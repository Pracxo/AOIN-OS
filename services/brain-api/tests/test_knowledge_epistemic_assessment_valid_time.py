"""AION-211 valid-time scope tests."""

from decimal import Decimal

from aion_brain.contracts.knowledge_epistemic_assessment import (
    EpistemicTargetScope,
    epistemic_target_scope_fingerprint,
)
from aion_brain.knowledge_intelligence.epistemic_assessment import (
    evaluate_valid_time_applicability,
)
from tests.test_knowledge_claim_graph_helpers import MUCH_LATER, claim, valid_interval, version


def test_valid_time_nonoverlap_is_not_applicable() -> None:
    payload = {
        "target_valid_time": valid_interval("interval-9001", start=MUCH_LATER, end=None),
        "target_jurisdiction_ids": ("global",),
        "target_version_scopes": (version(),),
    }
    target = EpistemicTargetScope(
        **payload,
        scope_fingerprint=epistemic_target_scope_fingerprint(payload),
    )
    applicability, factor = evaluate_valid_time_applicability(claim(), target)
    assert applicability == "not_applicable"
    assert factor == Decimal("0.000000")
