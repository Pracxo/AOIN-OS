"""Release package boundary tests."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RELEASE_PACKAGE_SRC = ROOT / "src" / "aion_brain" / "release_package"
PYPROJECT = ROOT / "pyproject.toml"


def test_release_package_service_has_no_subprocess_or_external_clients() -> None:
    forbidden = [
        "subprocess",
        "os.system",
        "httpx",
        "requests",
        "urllib",
        "boto",
        "langfuse",
    ]
    for path in RELEASE_PACKAGE_SRC.rglob("*.py"):
        text = path.read_text(encoding="utf-8").lower()
        for term in forbidden:
            assert term not in text, path


def test_release_package_task_adds_no_frontend_dependencies() -> None:
    pyproject = PYPROJECT.read_text(encoding="utf-8").lower()
    forbidden = ["react", "three", "rive", "lottie", "canvas", "langfuse"]

    for dependency in forbidden:
        assert dependency not in pyproject
