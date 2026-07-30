from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
AUTH_LEDGER = REPO_ROOT / "docs/governed-learning-memory/authorization-ledger.json"


def test_final_authorization_is_active_only_before_aion229_closeout() -> None:
    auth = json.loads(AUTH_LEDGER.read_text(encoding="utf-8"))
    record = next(
        item
        for item in auth["records"]
        if item["authorization_transaction_id"] == "AION-227-GLM-0004"
    )
    if auth["active_glm_implementation_authorization_count"] == 0:
        assert auth["active_glm_implementation_authorization"] is None
        assert auth["active_glm_implementation_task"] is None
        assert record["authorization_active"] is False
        assert record["authorization_consumed"] is True
        assert record["authorization_expired"] is True
        assert record["authorization_reusable"] is False
        assert record["authorization_consumed_by_task"] == "AION-228"
        assert record["authorization_consumed_by_prs"] == [145]
        assert record["authorization_consumed_by_feature_commits"] == [
            "07c146fe574a967266a2f2ad8b4473f51daf935d"
        ]
        assert record["authorization_consumed_by_merge_commits"] == [
            "0fc95c345c1f8daada58a5b45e6f3b1fdd33d9e0"
        ]
        assert record["authorization_closed_by_task"] == "AION-229"
    else:
        assert auth["active_glm_implementation_authorization_count"] == 1
        assert auth["active_glm_implementation_authorization"] == "AION-227-GLM-0004"
        assert auth["active_glm_implementation_task"] == "AION-228"
        assert record["authorization_active"] is True
        assert record["authorization_consumed"] is False
        assert record["authorization_expired"] is False
        assert record["authorization_reusable"] is False
