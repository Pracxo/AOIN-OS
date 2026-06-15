from __future__ import annotations

from pathlib import Path

import aion_sdk

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src" / "aion_sdk"
PYPROJECT = ROOT / "pyproject.toml"


def test_sdk_imports_without_server_package() -> None:
    assert aion_sdk.AIONClient.__name__ == "AIONClient"


def test_sdk_source_does_not_import_aion_brain() -> None:
    for path in SRC.rglob("*.py"):
        text = path.read_text()
        assert "aion_brain" not in text, path


def test_sdk_pyproject_has_no_database_provider_or_ui_dependencies() -> None:
    pyproject = PYPROJECT.read_text().lower()
    forbidden = [
        "sqlalchemy",
        "psycopg",
        "redis",
        "nats",
        "openai",
        "anthropic",
        "langfuse",
        "react",
        "three",
        "rive",
        "lottie",
        "canvas",
    ]

    for dependency in forbidden:
        assert dependency not in pyproject


def test_cli_has_no_domain_specific_commands() -> None:
    text = (SRC / "cli" / "main.py").read_text().lower()
    forbidden = ["finance", "trading", "legal", "healthcare", "medical", "procurement"]

    for term in forbidden:
        assert term not in text
