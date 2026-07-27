from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
AION215_SOURCE = (
    "services/brain-api/src/aion_brain/contracts/knowledge_tool_verification.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/tool_verification_fabric.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/tool_manifests.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/tool_planning.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/tool_simulation.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/tool_verification.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/tool_attestation.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/tool_effects.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/tool_integrity.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/tool_evidence.py",
)
PROHIBITED_AION215_RUNTIME_SURFACES = (
    "services/brain-api/src/aion_brain/api/tool_verification.py",
    "services/brain-api/src/aion_brain/api/knowledge_tool_verification.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/tool_runtime.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/tool_state_repository.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/tool_database.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/tool_worker.py",
)


def test_aion_215_source_is_exact_and_runtime_surfaces_are_absent() -> None:
    program = json.loads(
        (REPO_ROOT / "docs/knowledge-intelligence/program-ledger.json").read_text()
    )
    assert program["program_state"] in {
        "tool_verification_fabric_implemented_persistent_write_disabled_pending_closeout",
        "verified_knowledge_memory_authorized_not_implemented",
        "verified_knowledge_memory_implemented_persistent_write_disabled_pending_closeout",
        "controlled_public_research_pilot_authorized_not_implemented",
        "controlled_public_research_pilot_implemented_operator_invoked_persistent_write_disabled_pending_closeout",
        "knowledge_intelligence_program_complete",
    }
    assert program["tool_verification_fabric_implemented"] is True
    assert program["tool_verification_fabric_runtime_enabled"] is False
    assert program["actual_tool_execution_enabled"] is False
    assert program["persistent_tool_state_write_enabled"] is False

    for relative in AION215_SOURCE:
        assert (REPO_ROOT / relative).is_file(), relative

    for relative in PROHIBITED_AION215_RUNTIME_SURFACES:
        assert not (REPO_ROOT / relative).exists(), relative


def test_v02_tags_and_releases_are_not_repository_files() -> None:
    assert not (REPO_ROOT / "docs/release/v0.2.md").exists()
    assert not (REPO_ROOT / "docs/release/aion-v0.2.md").exists()
