from __future__ import annotations

from scripts.lib.governed_learning_memory_local_persistence_authorization import THREAT_MODEL
from test_governed_learning_memory_program_authorization import load_json


def test_future_threat_model_covers_required_classes() -> None:
    record = next(
        x
        for x in load_json("docs/governed-learning-memory/authorization-ledger.json")["records"]
        if x["authorization_transaction_id"] == "AION-223-GLM-0002"
    )
    assert record["threat_model"] == THREAT_MODEL
    for threat in [
        "database path traversal",
        "approval replay",
        "belief creation through projection",
        "production-memory contamination",
        "authorization reuse",
    ]:
        assert threat in record["threat_model"]
    assert (
        record["content_policy"]["confidential_content_allowed"] is False
        and record["content_policy"]["raw_source_body_allowed"] is False
    )
