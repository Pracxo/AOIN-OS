from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def test_operator_console_contract_script_passes() -> None:
    result = subprocess.run(
        [str(ROOT / "scripts/operator-console-contract-check.sh")],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    assert "Operator console contract check PASS" in result.stdout


def test_no_frontend_dependency_files_added() -> None:
    forbidden = {
        "package.json",
        "pnpm-lock.yaml",
        "yarn.lock",
        "package-lock.json",
        "vite.config.ts",
        "next.config.js",
        "tailwind.config.js",
    }
    paths = {
        path.name
        for path in ROOT.rglob("*")
        if path.is_file() and ".git" not in path.parts
    }

    assert forbidden.isdisjoint(paths)


def test_operator_console_docs_name_read_only_endpoints() -> None:
    readme = (ROOT / "README.md").read_text()
    cli = (ROOT / "docs/cli.md").read_text()

    assert "POST /brain/operator-console/view-model" in readme
    assert "POST /brain/operator-console/audit" in readme
    assert "aionctl operator-console views" in cli
