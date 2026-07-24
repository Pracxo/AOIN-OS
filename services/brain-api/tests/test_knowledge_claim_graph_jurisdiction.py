from __future__ import annotations

from test_knowledge_claim_graph_helpers import jurisdiction

from aion_brain.contracts.knowledge_claim_graph import JurisdictionKind
from aion_brain.knowledge_intelligence.claim_graph_temporal import jurisdiction_scopes_overlap


def test_jurisdiction_overlap_requires_explicit_scope_or_parentage() -> None:
    global_scope = (jurisdiction(),)
    gb = (jurisdiction("gb", JurisdictionKind.COUNTRY, ("global",)),)
    england = (jurisdiction("gb-eng", JurisdictionKind.SUBDIVISION, ("gb",)),)
    france = (jurisdiction("fr", JurisdictionKind.COUNTRY, ("global",)),)
    assert jurisdiction_scopes_overlap(global_scope, gb) == "overlap"
    assert jurisdiction_scopes_overlap(gb, england) == "overlap"
    assert jurisdiction_scopes_overlap(england, france) == "nonoverlap"
    assert jurisdiction_scopes_overlap((), gb) == "insufficient"
