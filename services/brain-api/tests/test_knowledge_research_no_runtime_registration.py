from __future__ import annotations

from pathlib import Path


def test_knowledge_research_package_has_no_api_or_kernel_registration():
    root = Path(__file__).resolve().parents[1] / "src/aion_brain/knowledge_intelligence"
    text = "\n".join(path.read_text() for path in root.glob("*.py"))
    for marker in ("include_router", "add_event_handler", "on_event", "startup", "create_task"):
        assert marker not in text
