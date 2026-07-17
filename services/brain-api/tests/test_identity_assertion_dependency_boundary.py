from __future__ import annotations

import importlib.metadata
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def test_exact_authorized_dependency_is_present() -> None:
    pyproject = tomllib.loads((ROOT / "services/brain-api/pyproject.toml").read_text())
    dependencies = pyproject["project"]["dependencies"]
    assert dependencies.count("cryptography>=49.0.0,<50.0.0") == 1
    assert not (ROOT / "services/brain-api/uv.lock").exists()
    assert not (ROOT / "services/brain-api/poetry.lock").exists()


def test_installed_cryptography_major_is_49() -> None:
    version = importlib.metadata.version("cryptography")
    assert version.split(".", 1)[0] == "49"
