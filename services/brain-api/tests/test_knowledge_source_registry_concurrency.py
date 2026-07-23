from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

from knowledge_source_registry_implementation_helpers import NOW, valid_batch, valid_evidence_bundle

from aion_brain.knowledge_intelligence.source_registry import (
    project_research_evidence_bundle,
)
from aion_brain.knowledge_intelligence.source_registry_index import (
    SourceRegistryQuery,
    build_source_registry_index,
    query_source_registry,
)


def test_source_registry_parallel_projection_and_queries_share_no_mutable_state():
    bundle = valid_evidence_bundle()
    with ThreadPoolExecutor(max_workers=4) as executor:
        batches = list(
            executor.map(
                lambda _item: project_research_evidence_bundle(bundle, clock=lambda: NOW),
                range(8),
            )
        )
    assert len({batch.batch_fingerprint for batch in batches}) == 1
    records = valid_batch().records
    index = build_source_registry_index(records)
    query = SourceRegistryQuery(
        query_id="query-class",
        query_kind="source_class",
        source_class="official_standard",
    )
    with ThreadPoolExecutor(max_workers=4) as executor:
        results = list(
            executor.map(lambda _item: query_source_registry(records, index, query), range(8))
        )
    assert len({result.query_fingerprint for result in results}) == 1
