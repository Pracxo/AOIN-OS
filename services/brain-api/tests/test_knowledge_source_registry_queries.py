from __future__ import annotations

from knowledge_source_registry_implementation_helpers import NOW, valid_batch

from aion_brain.knowledge_intelligence.source_registry_index import (
    SourceRegistryQuery,
    build_source_registry_index,
    query_source_registry,
)


def test_source_registry_queries_support_exact_indexes_and_time_ranges():
    records = valid_batch().records
    index = build_source_registry_index(records)
    snapshot = records[0].payload
    provenance = records[1].payload
    citation = records[2].payload
    lineage = records[3].payload
    queries = [
        SourceRegistryQuery(
            query_id="query-record",
            query_kind="record_id",
            value=records[0].record_id,
        ),
        SourceRegistryQuery(
            query_id="query-snapshot",
            query_kind="snapshot_fingerprint",
            value=snapshot.snapshot_fingerprint,
        ),
        SourceRegistryQuery(
            query_id="query-content",
            query_kind="content_sha256",
            value=snapshot.content_sha256,
        ),
        SourceRegistryQuery(
            query_id="query-provenance",
            query_kind="provenance_fingerprint",
            value=provenance.provenance_fingerprint,
        ),
        SourceRegistryQuery(
            query_id="query-citation",
            query_kind="citation_id",
            value=citation.citation_id,
        ),
        SourceRegistryQuery(
            query_id="query-lineage",
            query_kind="lineage_group_id",
            value=lineage.independence_group_id,
        ),
        SourceRegistryQuery(
            query_id="query-class",
            query_kind="source_class",
            source_class="official_standard",
        ),
        SourceRegistryQuery(
            query_id="query-time",
            query_kind="retrieval_time_range",
            retrieval_start=NOW,
            retrieval_end=NOW,
        ),
    ]
    for query in queries:
        result = query_source_registry(records, index, query)
        assert result.result_count >= 1
        assert result.runtime_effect is False


def test_source_registry_query_limit_is_enforced():
    records = valid_batch().records
    index = build_source_registry_index(records)
    result = query_source_registry(
        records,
        index,
        SourceRegistryQuery(
            query_id="query-class-limit",
            query_kind="source_class",
            source_class="official_standard",
            limit=1,
        ),
    )
    assert result.result_count == 1
    assert result.truncated is True
