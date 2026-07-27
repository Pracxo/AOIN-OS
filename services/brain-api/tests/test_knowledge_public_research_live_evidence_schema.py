from __future__ import annotations

import json
from pathlib import Path

from public_research_pilot_test_helpers import committed_live_evidence_path

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_committed_live_evidence_schema_is_redacted_when_present() -> None:
    path = REPO_ROOT / committed_live_evidence_path()
    if not path.exists():
        return
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["authorization_transaction_id"] == "AION-218-KI-0008"
    assert payload["mode"] == "operator_invoked_live"
    assert payload["source_bodies_retained"] == 0
    assert payload["operator_review_required"] is True
