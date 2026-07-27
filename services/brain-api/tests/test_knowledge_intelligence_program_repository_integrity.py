from __future__ import annotations

import os
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


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
    assert not {
        path for path in paths if path.startswith("services/brain-api/src/aion_brain/")
    }
    assert not {path for path in paths if path.startswith(".github/workflows/")}
