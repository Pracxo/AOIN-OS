from __future__ import annotations

import json

from test_knowledge_claim_graph_helpers import graph_repository


def test_graph_records_and_state_do_not_store_source_bodies_or_previews() -> None:
    repository = graph_repository()
    payload = json.dumps([record.model_dump(mode="json") for record in repository.records()])
    assert "source preview" not in payload.lower()
    assert "source body" not in payload.lower()
    assert all(record.source_body_present is False for record in repository.records())
    assert all(record.source_body_bytes == 0 for record in repository.records())
