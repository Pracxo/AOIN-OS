"""Extension Registry boundary guard tests."""

from __future__ import annotations

from pathlib import Path


def test_extension_registry_adds_no_frontend_or_runtime_loading_dependencies() -> None:
    root = Path(__file__).resolve().parents[3]
    extension_sources = list((root / "services/brain-api/src/aion_brain/extensions").glob("*.py"))
    joined = "\n".join(path.read_text() for path in extension_sources)

    assert "import subprocess" not in joined
    assert "pip install" not in joined
    assert "npm install" not in joined
    assert "docker run" not in joined
    assert "langfuse" not in joined.lower()
    assert "react" not in joined.lower()
    assert not (root / "frontend").exists()
