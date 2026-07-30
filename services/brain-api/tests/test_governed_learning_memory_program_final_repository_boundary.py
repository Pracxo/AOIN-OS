from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
HARNESS = REPO_ROOT / "scripts/lib/governed_learning_memory_program_final_evaluation.py"


def _load_harness():
    spec = importlib.util.spec_from_file_location("aion229_repository_boundary", HARNESS)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_final_repository_boundary_uses_existing_aion228_source_scope() -> None:
    harness = _load_harness()
    repository = harness.validate_repository_boundaries(REPO_ROOT)
    assert repository["repository_unchanged"] is True
    assert repository["workflows_changed"] is False
    assert repository["dependencies_changed"] is False
    assert repository["migrations_added"] is False
    assert repository["api_added"] is False
    assert repository["installed_cli_added"] is False
    assert set(repository["implemented_source_scope"]) == set(harness.IMPLEMENTED_SOURCE_SCOPE)
