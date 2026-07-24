from __future__ import annotations

import pytest
from pydantic import ValidationError
from test_knowledge_claim_graph_helpers import (
    LATER,
    MUCH_LATER,
    NOW,
    claim,
    jurisdiction,
    scope,
    valid_interval,
    version,
)


def test_claim_scope_is_explicit_and_fingerprinted() -> None:
    item = scope()
    changed = scope(intervals=(valid_interval("interval-0002", start=LATER, end=MUCH_LATER),))
    assert item.scope_fingerprint != changed.scope_fingerprint
    assert claim(claim_scope=item).scope.scope_fingerprint == item.scope_fingerprint


def test_scope_rejects_duplicate_or_overlapping_internal_dimensions() -> None:
    with pytest.raises(ValidationError):
        scope(
            jurisdictions=(
                jurisdiction("gb", parent_jurisdiction_ids=("global",)),
                jurisdiction("gb", parent_jurisdiction_ids=("global",)),
            )
        )
    with pytest.raises(ValidationError):
        scope(
            intervals=(
                valid_interval("interval-0001", start=NOW, end=LATER),
                valid_interval("interval-0002", start=NOW, end=MUCH_LATER),
            )
        )
    with pytest.raises(ValidationError):
        scope(versions=(version("standard-alpha", "1.0"), version("standard-alpha", "1.0")))
