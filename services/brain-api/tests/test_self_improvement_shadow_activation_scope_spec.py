"""AION-180 / AION-181 source-scope specification tests."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts/lib"))

from self_improvement_governance import (  # noqa: E402
    SHADOW_ACTIVATION_ALLOWED_CREATE,
    SHADOW_ACTIVATION_ALLOWED_UPDATE,
)


def test_aion181_runtime_source_is_absent_in_aion180() -> None:
    for relative in SHADOW_ACTIVATION_ALLOWED_CREATE:
        assert not (ROOT / relative).exists(), relative


def test_aion181_source_scope_is_exactly_recorded() -> None:
    record = _json("docs/self-improvement/authorization-ledger.json")["records"][-1]
    assert tuple(record["allowed_aion181_create_paths"]) == SHADOW_ACTIVATION_ALLOWED_CREATE
    assert tuple(record["allowed_aion181_update_paths"]) == SHADOW_ACTIVATION_ALLOWED_UPDATE
    assert "services/brain-api/src/aion_brain/self_improvement/shadow_mode.py" in record[
        "aion181_must_not_modify_paths"
    ]
    assert ".github/workflows/" in record["aion181_must_not_modify_paths"]
    assert "migrations/" in record["aion181_must_not_modify_paths"]


def test_aion180_branch_does_not_modify_runtime_or_package_surfaces() -> None:
    changed = subprocess.run(
        [
            "git",
            "diff",
            "--name-only",
            "origin/main...HEAD",
            "--",
            ".github/workflows",
            "services/brain-api/src/aion_brain",
            "services/brain-api/pyproject.toml",
            "packages/aion-sdk-python/src",
            "migrations",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    assert changed.stdout.strip() == ""


def _json(relative: str) -> dict[str, Any]:
    with (ROOT / relative).open() as handle:
        payload = json.load(handle)
    assert isinstance(payload, dict)
    return payload
