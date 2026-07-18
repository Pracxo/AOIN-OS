from __future__ import annotations

import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def test_pyproject_package_files_and_migrations_are_unchanged() -> None:
    changed = _changed_files()
    migration_name_allowlist = {
        "services/brain-api/tests/test_identity_assertion_replay_no_dependency_or_migration.py",
    }
    migration_named_changes = changed - migration_name_allowlist
    assert "services/brain-api/pyproject.toml" not in changed
    assert not any(path.startswith("migrations/") for path in changed)
    assert not any("migration" in Path(path).name.lower() for path in migration_named_changes)
    assert not any(path.endswith(("package.json", "package-lock.json")) for path in changed)
    assert not any(path.endswith(("pnpm-lock.yaml", "yarn.lock", "bun.lockb")) for path in changed)
    pyproject = (ROOT / "services/brain-api/pyproject.toml").read_text()
    assert pyproject.count('"cryptography>=49.0.0,<50.0.0",') == 1


def test_replay_repository_uses_existing_sqlalchemy_dependency_only() -> None:
    source = (
        ROOT
        / (
            "services/brain-api/src/aion_brain/production_auth/"
            "identity_assertion_replay_repository.py"
        )
    ).read_text()
    assert "from sqlalchemy" in source
    assert "alembic" not in source
    assert "create_all(self._engine)" in source


def _changed_files() -> set[str]:
    base = _comparison_base()
    if base is None:
        return set()
    diff = subprocess.run(
        ["git", "diff", "--name-only", base, "HEAD"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return {line.strip() for line in diff.stdout.splitlines() if line.strip()}


def _comparison_base() -> str | None:
    candidates: list[str] = []
    github_base_ref = os.environ.get("GITHUB_BASE_REF")
    if github_base_ref:
        candidates.extend([f"origin/{github_base_ref}", github_base_ref])
    candidates.extend(["origin/main", "main"])
    for candidate in candidates:
        if _git_ref_exists(candidate):
            merge_base = subprocess.run(
                ["git", "merge-base", "HEAD", candidate],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            if merge_base.returncode == 0 and merge_base.stdout.strip():
                return merge_base.stdout.strip()
    if _git_ref_exists("HEAD~1"):
        return "HEAD~1"
    return None


def _git_ref_exists(ref: str) -> bool:
    return (
        subprocess.run(
            ["git", "rev-parse", "--verify", "--quiet", ref],
            cwd=ROOT,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        ).returncode
        == 0
    )
