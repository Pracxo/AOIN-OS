from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
PROGRAM = REPO_ROOT / "docs/governed-learning-memory/program-ledger.json"
STATUS = REPO_ROOT / "docs/project-status.md"


def test_final_current_state_consistency_allows_pending_or_complete_aion229_state() -> None:
    program = json.loads(PROGRAM.read_text(encoding="utf-8"))
    status = STATUS.read_text(encoding="utf-8")
    assert "AION-229" in status
    if program.get("program_state") == "governed_learning_memory_program_complete":
        assert "Governed Learning and Memory Program complete" in status
        assert program["active_glm_implementation_authorization_count"] == 0
        assert program["formal_closeout_task"] is None
        assert program["v02_release_ready"] is False
    else:
        assert program["active_glm_implementation_authorization_count"] in {0, 1}
        assert program["formal_closeout_task"] == "AION-229"
