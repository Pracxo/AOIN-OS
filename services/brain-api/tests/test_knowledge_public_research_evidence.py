from __future__ import annotations

from public_research_pilot_test_helpers import run_simulation


def test_evidence_bundle_is_redacted_and_non_persistent() -> None:
    bundle = run_simulation().evidence_bundle
    assert bundle.redacted is True
    assert bundle.source_bodies_persisted == 0
    assert bundle.persistent_verified_knowledge_writes == 0
