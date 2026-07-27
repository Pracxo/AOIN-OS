from __future__ import annotations

import pytest
from public_research_pilot_test_helpers import make_claim

from aion_brain.knowledge_intelligence.public_research_claims import (
    bind_explicit_claim_specifications,
)


def test_claim_binding_requires_explicit_resolving_evidence() -> None:
    claim = make_claim()
    bindings = bind_explicit_claim_specifications(
        (claim,),
        available_source_snapshot_ids=("public-research-source-snapshot-0001",),
        available_citation_ids=(),
    )
    assert bindings[0].automatic_claim_extraction_enabled is False
    with pytest.raises(ValueError):
        bind_explicit_claim_specifications(
            (claim,), available_source_snapshot_ids=(), available_citation_ids=()
        )
