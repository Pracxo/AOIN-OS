from __future__ import annotations

from test_knowledge_source_snapshot import valid_snapshot

from aion_brain.knowledge_intelligence.source_deduplication import deduplicate_source_snapshots


def test_deduplication_groups_exact_content_without_deleting_snapshots():
    one = valid_snapshot()
    two = one.model_copy(
        update={
            "snapshot_id": "source-snapshot-0002",
            "canonical_url": "https://standards.example.invalid/source.txt",
            "final_url": "https://standards.example.invalid/source.txt",
            "snapshot_fingerprint": "c" * 64,
        }
    )
    decisions = deduplicate_source_snapshots((one, two))
    assert len(decisions) == 2
    assert all(decision.exact_content_duplicate for decision in decisions)
    assert decisions[0].independence_group_id == decisions[1].independence_group_id
    assert any("research_exact_content_duplicate" in d.reason_codes for d in decisions)
