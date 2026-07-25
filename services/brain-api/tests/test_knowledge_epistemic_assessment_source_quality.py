"""AION-211 source-quality metadata tests."""

from decimal import Decimal

from aion_brain.knowledge_intelligence.epistemic_corroboration import source_quality_factor


def test_source_quality_metadata_factors_are_versioned() -> None:
    assert source_quality_factor("official_standard") == Decimal("1.000000")
    assert source_quality_factor("community_unverified") == Decimal("0.350000")
    assert source_quality_factor("unknown") == Decimal("0.250000")
