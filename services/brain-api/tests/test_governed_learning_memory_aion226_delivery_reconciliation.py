from __future__ import annotations

from pathlib import Path

from scripts.lib import governed_learning_memory_continual_learning_pilot_authorization as auth227

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_aion226_delivery_records_feature_corrective_and_merge_evidence() -> None:
    program, _ = auth227.validate_ledgers(REPO_ROOT)
    delivery = program["aion_226_delivery"]
    assert delivery["pull_requests"] == [142, 143]
    assert delivery["feature_commits"] == auth227.PARENT_FEATURE_COMMITS
    assert delivery["merge_commits"] == auth227.PARENT_MERGE_COMMITS
    assert delivery["ci_result"] == "pass"
    assert delivery["completion_timestamp"] == auth227.AION226_COMPLETION_TIMESTAMP
    assert delivery["evaluation_id"] == "AION-GLMPE-003"
