from __future__ import annotations

from aion_brain.beliefs.normalizer import hash_normalized_claim, normalize_claim_text


def test_claim_normalizer_preserves_negation() -> None:
    assert normalize_claim_text("Not ready.").startswith("not ")


def test_claim_hash_is_deterministic() -> None:
    normalized = normalize_claim_text("The system is ready.")
    assert hash_normalized_claim(normalized) == hash_normalized_claim(normalized)
