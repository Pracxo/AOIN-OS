"""AION-211 confidence-band tests."""

from decimal import Decimal

from aion_brain.contracts.knowledge_epistemic_assessment import confidence_band_for


def test_confidence_bands_are_bounded() -> None:
    assert confidence_band_for(Decimal("0.100000")) == "very_low"
    assert confidence_band_for(Decimal("0.500000")) == "medium"
    assert confidence_band_for(Decimal("0.900000")) == "very_high"
