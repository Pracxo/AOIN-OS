from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
THREAT_MODEL = REPO_ROOT / "docs/knowledge-intelligence/public-research-pilot-threat-model.md"


def test_public_research_pilot_threat_model_names_required_threats() -> None:
    text = THREAT_MODEL.read_text(encoding="utf-8")
    for marker in (
        "SSRF",
        "DNS rebinding",
        "metadata-service",
        "private-network",
        "redirect downgrade",
        "certificate mismatch",
        "credential leakage",
        "prompt injection",
        "background crawling",
        "evaluation evidence used as approval",
    ):
        assert marker in text
