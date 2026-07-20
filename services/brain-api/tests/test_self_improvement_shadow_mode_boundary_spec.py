"""AION-177 shadow-mode boundary specification tests."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts/lib"))

from self_improvement_governance import (  # noqa: E402
    AION178_ALLOWED_CREATE,
    SHADOW_ALLOWED_INPUTS,
    SHADOW_DISALLOWED_INPUTS,
    SHADOW_PROHIBITED_SCOPE,
)


def test_boundary_doc_keeps_write_and_runtime_actions_out_of_scope() -> None:
    text = (ROOT / "docs/self-improvement/shadow-mode-boundary.md").read_text()
    for phrase in (
        "Source mutation",
        "Git write",
        "Pull request creation",
        "Production canary",
        "Production deployment",
        "External provider calls",
        "Connector runtime calls",
        "v0.2 tag or release creation",
    ):
        assert phrase in text


def test_data_boundary_lists_allowed_and_disallowed_inputs() -> None:
    payload = _json("examples/self-improvement/shadow-mode-data-boundary.json")
    assert tuple(payload["allowed_inputs"]) == SHADOW_ALLOWED_INPUTS
    assert tuple(payload["disallowed_inputs"]) == SHADOW_DISALLOWED_INPUTS


def test_aion178_creates_only_scoped_shadow_runtime_source() -> None:
    for relative in AION178_ALLOWED_CREATE:
        assert (ROOT / relative).is_file(), relative
    authorization = _json("docs/self-improvement/authorization-ledger.json")
    prohibited = tuple(authorization["records"][-1]["prohibited_scope"])
    assert prohibited == SHADOW_PROHIBITED_SCOPE


def _json(relative: str) -> dict[str, Any]:
    with (ROOT / relative).open() as handle:
        payload = json.load(handle)
    assert isinstance(payload, dict)
    return payload
