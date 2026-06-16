from __future__ import annotations

from aion_brain.concepts.normalizer import normalize_concept_name
from aion_brain.entities.normalizer import normalize_entity_name


def test_entity_normalizer_is_case_and_spacing_stable() -> None:
    assert normalize_entity_name("  Test   Reference  ") == "test reference"


def test_concept_normalizer_strips_unsafe_punctuation() -> None:
    assert normalize_concept_name("Generic@@ Concept") == "generic concept"
