"""AION-180 threat-model tests."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts/lib"))

from self_improvement_governance import SHADOW_ACTIVATION_THREATS  # noqa: E402


def test_threat_model_documents_every_required_threat() -> None:
    record = _json("docs/self-improvement/authorization-ledger.json")["records"][-1]
    text = _text("docs/self-improvement/shadow-activation-threat-model.md")
    assert tuple(record["threats_addressed"]) == SHADOW_ACTIVATION_THREATS
    for threat in SHADOW_ACTIVATION_THREATS:
        assert threat in text


def test_core_rule_prevents_activation_confusion() -> None:
    text = _text("docs/self-improvement/shadow-activation-threat-model.md")
    assert "authorizes construction of a disabled activation control plane" in text
    assert "It does not authorize activation" in text
    assert "evaluation PASS mistaken for activation approval" in text
    assert "AION-177-SI-0006 reuse" in text
    assert "production activation without another authorization" in text


def _json(relative: str) -> dict[str, Any]:
    with (ROOT / relative).open() as handle:
        payload = json.load(handle)
    assert isinstance(payload, dict)
    return payload


def _text(relative: str) -> str:
    return (ROOT / relative).read_text()
