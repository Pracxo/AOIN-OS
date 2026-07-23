from __future__ import annotations

from pathlib import Path

import aion_brain.knowledge_intelligence.source_registry as source_registry
from aion_brain.knowledge_intelligence.source_registry_repository import (
    InMemorySourceRegistryRepository,
)

ROOT = Path(__file__).resolve().parents[3]


def test_source_registry_has_no_runtime_api_cli_scheduler_or_database_surface():
    assert not (ROOT / "services/brain-api/src/aion_brain/api/source_registry.py").exists()
    assert not (
        ROOT / "services/brain-api/src/aion_brain/knowledge_intelligence/source_registry_runtime.py"
    ).exists()
    assert not (
        ROOT / "services/brain-api/src/aion_brain/knowledge_intelligence/source_registry_service.py"
    ).exists()
    for name in ("socket", "subprocess", "sqlite3", "requests", "httpx", "aiohttp"):
        assert name not in source_registry.__dict__
    repository = InMemorySourceRegistryRepository()
    assert not hasattr(repository, "background_worker")
    assert not hasattr(repository, "scheduler")
    assert not hasattr(repository, "database")
