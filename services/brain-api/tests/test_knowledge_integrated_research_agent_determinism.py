from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
VALIDATOR = REPO_ROOT / "scripts/lib/knowledge_intelligence_verified_knowledge_authorization.py"
HARNESS = (
    REPO_ROOT
    / "scripts/lib/knowledge_intelligence_integrated_research_agent_operator_evaluation.py"
)


def _load_validator():
    sys.path.insert(0, str(REPO_ROOT / "scripts/lib"))
    spec = importlib.util.spec_from_file_location("verified_auth", VALIDATOR)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _load_json(relative: str) -> dict[str, object]:
    return json.loads((REPO_ROOT / relative).read_text(encoding="utf-8"))


def test_integrated_report_is_deterministic_for_fixed_input(tmp_path: Path) -> None:
    spec = importlib.util.spec_from_file_location("harness", HARNESS)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    first = module.evaluate_integrated_research_agent(
        repo_root=REPO_ROOT,
        evaluation_id="AION-IRAE-001",
        evaluation_base_commit="eab135b7b0225c79917b5930da057422bf1dbeed",
        temporary_output_directory=tmp_path / "a",
    )
    second = module.evaluate_integrated_research_agent(
        repo_root=REPO_ROOT,
        evaluation_id="AION-IRAE-001",
        evaluation_base_commit="eab135b7b0225c79917b5930da057422bf1dbeed",
        temporary_output_directory=tmp_path / "b",
    )
    changed = module.evaluate_integrated_research_agent(
        repo_root=REPO_ROOT,
        evaluation_id="AION-IRAE-001",
        evaluation_base_commit="different",
        temporary_output_directory=tmp_path / "c",
    )
    assert (
        first["integrated_lineage"]["integrated_trace_fingerprint"]
        == second["integrated_lineage"]["integrated_trace_fingerprint"]
    )
    assert (
        changed["integrated_lineage"]["integrated_trace_fingerprint"]
        != first["integrated_lineage"]["integrated_trace_fingerprint"]
    )
