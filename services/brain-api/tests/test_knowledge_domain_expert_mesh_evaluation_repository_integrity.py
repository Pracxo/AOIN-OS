from __future__ import annotations

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


def test_aion_214_does_not_create_aion_215_runtime_source() -> None:
    for relative in AION215_SOURCE:
        assert not (REPO_ROOT / relative).exists(), relative


def test_v02_tags_and_releases_are_not_repository_files() -> None:
    assert not (REPO_ROOT / "docs/release/v0.2.md").exists()
    assert not (REPO_ROOT / "docs/release/aion-v0.2.md").exists()
