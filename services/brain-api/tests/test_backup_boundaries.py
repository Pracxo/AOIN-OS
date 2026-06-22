"""Backup boundary tests."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKUP_SRC = ROOT / "src" / "aion_brain" / "backups"
PYPROJECT = ROOT / "pyproject.toml"


def test_backup_services_have_no_external_clients_or_database_dump_calls() -> None:
    forbidden = [
        "pg_dump",
        "subprocess",
        "os.system",
        "httpx",
        "requests",
        "urllib",
        "boto",
        "s3",
        "gcs",
        "azure",
        "langfuse",
    ]
    for path in BACKUP_SRC.rglob("*.py"):
        text = path.read_text(encoding="utf-8").lower()
        for term in forbidden:
            assert term not in text, path


def test_backup_task_adds_no_frontend_dependencies() -> None:
    pyproject = PYPROJECT.read_text(encoding="utf-8").lower()
    forbidden = ["react", "three", "rive", "lottie", "canvas", "langfuse"]

    for dependency in forbidden:
        assert dependency not in pyproject
