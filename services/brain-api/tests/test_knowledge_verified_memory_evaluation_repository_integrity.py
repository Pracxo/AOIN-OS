from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
PUBLIC_PILOT_SOURCE = (
    REPO_ROOT
    / "services/brain-api/src/aion_brain/knowledge_intelligence/public_research_pilot.py"
)


def load_json(relative: str) -> dict[str, object]:
    return json.loads((REPO_ROOT / relative).read_text(encoding="utf-8"))


def report() -> dict[str, object]:
    return load_json(
        "examples/knowledge-intelligence/verified-memory-operator-evaluation-report.json"
    )


def test_repository_integrity_records_no_runtime_or_future_source() -> None:
    program = load_json("docs/knowledge-intelligence/program-ledger.json")
    public_pilot_implemented_state = (
        "controlled_public_research_pilot_implemented_operator_invoked_"
        "persistent_write_disabled_pending_closeout"
    )
    if program["program_state"] == public_pilot_implemented_state:
        assert PUBLIC_PILOT_SOURCE.exists()
        assert program["public_network_fetch_enabled"] is False
        assert program["persistent_verified_knowledge_write_enabled"] is False
        return

    integrity = report()["repository_integrity"]
    for key in (
        "runtime_source_changed",
        "aion_219_source_created",
        "network_source_created",
        "workflow_changed",
        "dependency_changed",
        "migration_added",
        "api_added",
        "cli_added",
        "database_added",
    ):
        assert integrity[key] is False
    assert not PUBLIC_PILOT_SOURCE.exists()
