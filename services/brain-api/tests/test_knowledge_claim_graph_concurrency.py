from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

from test_knowledge_claim_graph_helpers import (
    graph_batch,
    graph_repository,
    source_registry_repository,
)

from aion_brain.knowledge_intelligence.claim_graph_index import ClaimGraphQuery


def test_parallel_projection_query_and_audit_share_no_mutable_state() -> None:
    def project_once() -> str:
        return graph_batch()[3].batch_fingerprint

    repository = graph_repository()
    service, registry, _claims, _batch = graph_batch()
    with ThreadPoolExecutor(max_workers=4) as pool:
        projections = tuple(pool.map(lambda _item: project_once(), range(8)))
        queries = tuple(
            pool.map(
                lambda _item: (
                    service.query(
                        repository,
                        ClaimGraphQuery(
                            query_id="query-0001", query_kind="claim_id", value="claim-0001"
                        ),
                    ).query_fingerprint
                ),
                range(8),
            )
        )
        audits = tuple(
            pool.map(
                lambda _item: (
                    service.audit(
                        repository, source_registry_repository=registry
                    ).report_fingerprint
                ),
                range(8),
            )
        )
    assert len(set(projections)) == 1
    assert len(set(queries)) == 1
    assert len(set(audits)) == 1
    assert source_registry_repository().record_count() == 4
