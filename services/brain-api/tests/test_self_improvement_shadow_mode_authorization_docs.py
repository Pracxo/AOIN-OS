"""AION-177 shadow-mode authorization documentation tests."""

from __future__ import annotations

import json
import os
import stat
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts/lib"))

from self_improvement_governance import (  # noqa: E402
    AION177_REQUIRED_DOCS,
    AION177_REQUIRED_EXAMPLES,
    SHADOW_AUTHORIZATION_ID,
    SHADOW_IMPLEMENTATION_TASK,
    validate_repo,
)


def test_shadow_mode_authorization_artifacts_are_present_and_indexed() -> None:
    validate_repo(ROOT)
    for relative in (*AION177_REQUIRED_DOCS, *AION177_REQUIRED_EXAMPLES):
        assert (ROOT / relative).is_file(), relative

    adr_index = (ROOT / "docs/adr/README.md").read_text()
    assert "0162-controlled-self-improvement-shadow-mode-authorization.md" in adr_index


def test_shadow_mode_authorization_scripts_are_executable() -> None:
    for relative in (
        "scripts/self-improvement-shadow-mode-authorization-check.sh",
        "scripts/self-improvement-shadow-mode-authorization-no-go-regression.sh",
        "scripts/self-improvement-shadow-mode-runtime-hold.sh",
    ):
        mode = os.stat(ROOT / relative).st_mode
        assert mode & stat.S_IXUSR, relative


def test_shadow_mode_static_console_evidence_is_read_only() -> None:
    payload = _json(
        "operator-console-static/demo-data/self-improvement-shadow-mode-plane.json"
    )
    assert payload["authorization_transaction_id"] == SHADOW_AUTHORIZATION_ID
    assert payload["implementation_task"] == SHADOW_IMPLEMENTATION_TASK
    assert payload["synthetic"] is True
    assert payload["read_only"] is True
    assert payload["shadow_mode"] is True
    assert payload["shadow_mode_implemented"] is True
    assert payload["shadow_mode_runtime_enabled"] is False
    assert payload["runtime_effect"] is False
    assert payload["diagnostics"]["network_calls"] == 0


def _json(relative: str) -> dict[str, Any]:
    with (ROOT / relative).open() as handle:
        payload = json.load(handle)
    assert isinstance(payload, dict)
    return payload
