from __future__ import annotations

from test_governed_learning_memory_contracts import source_text


def test_source_does_not_register_routes_clis_or_runtime_workers():
    text = source_text()

    assert "APIRouter" not in text
    assert "FastAPI" not in text
    assert "click.command" not in text
    assert "celery" not in text.lower()
    assert "runtime_effect: Literal[False]" in text
