"""Visual projection safety and boundary tests."""

from pathlib import Path


def test_visual_projection_has_no_frontend_or_langfuse_sdk_dependencies() -> None:
    """AION-020 remains backend-only and does not import Langfuse."""
    root = Path(__file__).parents[1] / "src" / "aion_brain"
    visual_source = "\n".join(path.read_text() for path in (root / "visual").glob("*.py"))
    observability_source = "\n".join(
        path.read_text() for path in (root / "observability").glob("*.py")
    )
    prohibited = ("react", "three.js", "rive", "lottie", "canvas")

    assert all(term not in visual_source.lower() for term in prohibited)
    assert "import langfuse" not in observability_source.lower()
    assert "from langfuse" not in observability_source.lower()
