from __future__ import annotations

import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]


def test_verified_memory_operator_evaluation_scripts_are_executable_and_pass() -> None:
    scripts = (
        "scripts/knowledge-intelligence-verified-memory-operator-evaluation-no-go-regression.sh",
        "scripts/knowledge-intelligence-verified-memory-operator-evaluation-check.sh",
    )
    for script in scripts:
        path = REPO_ROOT / script
        assert path.exists()
        assert path.stat().st_mode & 0o111
        subprocess.run([str(path)], cwd=REPO_ROOT, check=True)
