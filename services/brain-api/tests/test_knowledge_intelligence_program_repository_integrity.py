from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


def _aion239_source_paths() -> set[str]:
    program = json.loads(
        (REPO_ROOT / "docs/v02-release-qualification/program-ledger.json").read_text()
    )
    if (
        program.get("active_v02_release_qualification_task") != "AION-239"
        or program.get("v02_release_qualification_foundation_implemented") is not True
        or program.get("foundation_runtime_state")
        != "implemented_disabled_design_only_local_simulation"
    ):
        return set()
    source_scope = program.get("implemented_source_scope")
    assert isinstance(source_scope, list)
    return {str(path) for path in source_scope}


def _assert_aion239_boundaries(paths: set[str]) -> None:
    changed = paths & _aion239_source_paths()
    if changed:
        assert changed <= _aion239_source_paths()
        assert not (
            REPO_ROOT
            / "services/brain-api/src/aion_brain/api/v02_release_qualification.py"
        ).exists()


def test_program_final_evaluation_no_go_script_passes() -> None:
    env = {**os.environ, "PYTEST_CURRENT_TEST": "AION-220 no-go"}
    script = (
        REPO_ROOT
        / "scripts/knowledge-intelligence-program-final-evaluation-no-go-regression.sh"
    )
    subprocess.run(
        [str(script)],
        cwd=REPO_ROOT,
        env=env,
        check=True,
    )


def test_program_final_evaluation_branch_does_not_modify_runtime_source() -> None:
    changed = subprocess.run(
        ["git", "diff", "--name-only", "origin/main...HEAD"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    paths = {line.strip() for line in changed.stdout.splitlines() if line.strip()}
    aion239_source_paths = _aion239_source_paths()
    assert not {
        path
        for path in paths
        if path.startswith("services/brain-api/src/aion_brain/")
        and path not in aion239_source_paths
    }
    _assert_aion239_boundaries(paths)
    assert not {path for path in paths if path.startswith(".github/workflows/")}
