from __future__ import annotations

from decimal import Decimal

import pytest
from pydantic import ValidationError
from test_knowledge_claim_graph_helpers import (
    boolean_object,
    identifier_object,
    integer_object,
    text_object,
)

from aion_brain.contracts.knowledge_claim_graph import (
    DecimalClaimObjectValue,
    QuantityClaimObjectValue,
    VersionClaimObjectValue,
    VersionScheme,
    claim_object_value_fingerprint,
)


def test_typed_object_values_are_deterministic_and_fingerprinted() -> None:
    assert text_object("alpha").object_fingerprint != text_object("beta").object_fingerprint
    assert identifier_object().kind == "identifier"
    assert boolean_object().canonical_value is True
    assert integer_object().canonical_value == 42
    decimal = DecimalClaimObjectValue(
        canonical_value=Decimal("1.25"),
        display_value="1.25",
        object_fingerprint=claim_object_value_fingerprint(
            kind="decimal",
            canonical_value=Decimal("1.25"),
        ),
    )
    assert decimal.canonical_value == Decimal("1.25")


def test_object_values_reject_source_content_urls_and_bad_versions() -> None:
    with pytest.raises(ValidationError):
        text_object("https://example.invalid/source")
    with pytest.raises(ValidationError):
        QuantityClaimObjectValue(
            canonical_value=Decimal("1"),
            unit_id="../kg",
            display_value="1 kg",
            object_fingerprint=claim_object_value_fingerprint(
                kind="quantity",
                canonical_value=Decimal("1"),
                unit_id="../kg",
            ),
        )
    with pytest.raises(ValidationError):
        VersionClaimObjectValue(
            canonical_value="1.alpha",
            scheme=VersionScheme.NUMERIC_DOTTED_EXACT,
            display_value="1.alpha",
            object_fingerprint=claim_object_value_fingerprint(
                kind="version",
                canonical_value="1.alpha",
                scheme=VersionScheme.NUMERIC_DOTTED_EXACT,
            ),
        )
