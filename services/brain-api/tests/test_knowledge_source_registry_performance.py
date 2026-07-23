from __future__ import annotations

import json

from knowledge_source_registry_implementation_helpers import (
    NOW,
    fixture_payload,
    valid_batch,
    valid_evidence_bundle,
)

from aion_brain.contracts.knowledge_source_registry import SourceRegistryProposedBatch
from aion_brain.knowledge_intelligence.source_registry import project_research_evidence_bundle
from aion_brain.knowledge_intelligence.source_registry_index import (
    SourceRegistryQuery,
    build_source_registry_index,
    query_source_registry,
)
from aion_brain.knowledge_intelligence.source_registry_integrity import (
    audit_source_registry,
    calculate_record_fingerprint,
    validate_record_envelope,
)
from aion_brain.knowledge_intelligence.source_registry_repository import (
    ExplicitLocalSourceRegistryFixtureReplay,
    InMemorySourceRegistryRepository,
)


def test_source_registry_ci_safe_performance_smoke(tmp_path):
    bundle = valid_evidence_bundle()
    batch = valid_batch()
    records = batch.records
    for index in range(10_000):
        validate_record_envelope(records[index % len(records)])
    for index in range(5_000):
        calculate_record_fingerprint(records[index % len(records)])
    payload = batch.model_dump(mode="json")
    for _index in range(2_000):
        SourceRegistryProposedBatch.model_validate(payload)
    for _index in range(1_000):
        project_research_evidence_bundle(bundle, clock=lambda: NOW)
    for _index in range(1_000):
        InMemorySourceRegistryRepository().with_simulated_append(batch)
    for _index in range(1_000):
        index = build_source_registry_index(records)
    for _index in range(1_000):
        audit_source_registry(records, clock=lambda: NOW)
    query = SourceRegistryQuery(
        query_id="query-record",
        query_kind="record_id",
        value=records[0].record_id,
    )
    for _index in range(5_000):
        query_source_registry(records, index, query)
    fixture = tmp_path / "source-registry-fixture.json"
    fixture.write_text(json.dumps(fixture_payload(records)), encoding="utf-8")
    replay = ExplicitLocalSourceRegistryFixtureReplay()
    for _index in range(500):
        replay.replay(fixture, repository_root="/Users/damilaremerotiwon/KITEV2/AOIN OS")
