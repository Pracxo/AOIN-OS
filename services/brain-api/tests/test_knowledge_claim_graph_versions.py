from __future__ import annotations

import pytest
from pydantic import ValidationError
from test_knowledge_claim_graph_helpers import version

from aion_brain.contracts.knowledge_claim_graph import (
    VersionScheme,
    VersionScope,
    version_scope_fingerprint,
)
from aion_brain.knowledge_intelligence.claim_graph_temporal import version_scopes_overlap


def test_version_overlap_uses_numeric_tuples_and_target_match() -> None:
    exact = (version("standard-alpha", "1.2"),)
    ranged = (
        VersionScope(
            target_id="standard-alpha",
            scheme=VersionScheme.NUMERIC_DOTTED_RANGE,
            lower_bound="1.0",
            upper_bound="1.10",
            scope_fingerprint=version_scope_fingerprint(
                target_id="standard-alpha",
                scheme=VersionScheme.NUMERIC_DOTTED_RANGE,
                lower_bound="1.0",
                upper_bound="1.10",
            ),
        ),
    )
    other = (version("standard-beta", "1.2"),)
    assert version_scopes_overlap(exact, ranged) == "overlap"
    assert version_scopes_overlap(exact, other) == "nonoverlap"
    assert version_scopes_overlap((), exact) == "insufficient"
    with pytest.raises(ValidationError):
        VersionScope(
            target_id="standard-alpha",
            scheme=VersionScheme.OPAQUE_EXACT,
            lower_bound="1.0",
            scope_fingerprint=version_scope_fingerprint(
                target_id="standard-alpha",
                scheme=VersionScheme.OPAQUE_EXACT,
                lower_bound="1.0",
            ),
        )
