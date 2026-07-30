from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
PROGRAM = REPO_ROOT / "docs/governed-learning-memory/program-ledger.json"


def test_final_reconciliation_state_is_pending_or_complete_without_successor_task() -> None:
    program = json.loads(PROGRAM.read_text(encoding="utf-8"))
    if program.get("program_state") == "governed_learning_memory_program_complete":
        assert program["governed_learning_memory_program_complete"] is True
        assert program["formal_closeout_task"] is None
        assert program["active_glm_implementation_authorization_count"] == 0
        assert program["active_glm_implementation_authorization"] is None
        assert program["active_glm_implementation_task"] is None
        assert program["next_glm_implementation_authorization"] is None
        assert program["next_glm_implementation_task"] is None
        assert program["final_completed_task"] == "AION-229"
    else:
        assert program["formal_closeout_task"] == "AION-229"
        assert program.get("next_glm_implementation_task") is None
