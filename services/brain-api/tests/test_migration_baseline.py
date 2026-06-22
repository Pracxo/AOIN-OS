"""Migration baseline tests."""

from __future__ import annotations

from pathlib import Path

from aion_brain.versioning.migrations import (
    DESTRUCTIVE_OVERRIDE,
    MigrationBaselineService,
    analyze_migration_files,
)
from tests.versioning_fakes import SCOPE, AllowPolicy, repository


def test_migration_baseline_detects_tables_and_hash(tmp_path: Path) -> None:
    migrations = tmp_path / "migrations"
    migrations.mkdir()
    (migrations / "0001_create.py").write_text(
        "def upgrade():\n    op.create_table('aion_events')\n",
        encoding="utf-8",
    )
    service = MigrationBaselineService(repository(), AllowPolicy(), migrations_dir=migrations)

    baseline = service.generate("0.1.0", SCOPE)

    assert baseline.status == "passed"
    assert baseline.tables == ["aion_events"]
    assert baseline.migration_hash


def test_migration_baseline_flags_destructive_upgrade(tmp_path: Path) -> None:
    migrations = tmp_path / "migrations"
    migrations.mkdir()
    (migrations / "0002_drop.py").write_text(
        "def upgrade():\n    op.drop_table('aion_old')\n",
        encoding="utf-8",
    )

    destructive, _, _ = analyze_migration_files(migrations)

    assert destructive == ["0002_drop.py"]


def test_migration_baseline_allows_explicit_override(tmp_path: Path) -> None:
    migrations = tmp_path / "migrations"
    migrations.mkdir()
    (migrations / "0003_drop.py").write_text(
        f"# {DESTRUCTIVE_OVERRIDE}\ndef upgrade():\n    op.drop_table('aion_old')\n",
        encoding="utf-8",
    )

    destructive, _, _ = analyze_migration_files(migrations)

    assert destructive == []
