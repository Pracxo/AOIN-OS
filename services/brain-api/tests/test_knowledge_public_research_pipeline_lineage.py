from __future__ import annotations

from public_research_pilot_test_helpers import run_simulation


def test_pipeline_lineage_has_snapshots_provenance_and_citations() -> None:
    session = run_simulation().session
    assert session.source_snapshot_fingerprints
    assert session.source_provenance_fingerprints
    assert session.citation_fingerprints
