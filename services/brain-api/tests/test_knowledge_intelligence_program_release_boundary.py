from __future__ import annotations

import json
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_program_closeout_does_not_create_v02_release_or_tag() -> None:
    program = json.loads(
        (REPO_ROOT / "docs/knowledge-intelligence/program-ledger.json").read_text(
            encoding="utf-8"
        )
    )
    assert program.get("v02_release_ready", False) is False
    assert program.get("v02_tag_created", False) is False
    assert program.get("v02_release_created", False) is False
    tags = subprocess.run(
        ["git", "tag", "-l", "v0.2*", "aion-v0.2*"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    assert set(tags.stdout.splitlines()) <= {"aion-v0.2.0-rc.1"}


def test_aion_v010_tag_still_exists() -> None:
    result = subprocess.run(
        ["git", "show-ref", "--tags", "aion-v0.1.0"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    assert "105fe29348160a2218ac095cfffadcb6f234421f refs/tags/aion-v0.1.0" in result.stdout
