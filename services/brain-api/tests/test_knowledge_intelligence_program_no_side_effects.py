from __future__ import annotations

import ast
import importlib.util
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
HARNESS = REPO_ROOT / "scripts/lib/knowledge_intelligence_program_final_evaluation.py"


def _load_harness():
    spec = importlib.util.spec_from_file_location("aion220_no_side_effects", HARNESS)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_final_evaluation_report_records_zero_side_effects(tmp_path: Path) -> None:
    harness = _load_harness()
    payload = harness.evaluate_program(
        repo_root=REPO_ROOT,
        evaluation_id="AION-KIPE-001",
        evaluation_base_commit="d0e1807edd7b3098ce62f8d00b0bceb4ee6fd23d",
        temporary_output_directory=tmp_path,
    )
    for key, value in harness.ZERO_EFFECT_FIELDS.items():
        assert payload[key] == value
    assert payload["evaluation_network_requests"] == 0
    assert payload["deterministic_public_research_replay"]["dns_resolutions"] == 2
    assert payload["deterministic_public_research_replay"]["public_https_requests"] == 2


def test_final_evaluation_harness_has_no_forbidden_runtime_imports() -> None:
    tree = ast.parse(HARNESS.read_text(encoding="utf-8"), filename=str(HARNESS))
    prohibited = {
        "socket",
        "ssl",
        "requests",
        "httpx",
        "aiohttp",
        "urllib.request",
        "sqlite3",
        "subprocess",
        "selenium",
        "playwright",
        "openai",
        "anthropic",
    }
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module)
    assert not {name for name in imports if name in prohibited}
