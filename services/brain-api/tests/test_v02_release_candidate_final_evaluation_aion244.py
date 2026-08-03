from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
EVALUATOR_PATH = REPO_ROOT / "scripts/lib/v02_release_candidate_final_evaluation.py"
REPORT_PATH = (
    REPO_ROOT
    / "examples"
    / "v02-release-qualification"
    / "v02-release-candidate-final-evaluation-report.json"
)


def load_evaluator():
    spec = importlib.util.spec_from_file_location("aion244_eval", EVALUATOR_PATH)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_aion_244_evaluator_defines_exact_32_hard_gate_scenarios() -> None:
    module = load_evaluator()

    assert module.EVALUATION_ID == "AION-V02RQPE-003"
    assert module.CANDIDATE_ID == "aion-v0.2.0-rc.1"
    assert module.PACKAGE_VERSION == "0.2.0rc1"
    assert module.CANDIDATE_SOURCE_COMMIT == "d35f1caa234d35dce1dfc0a80bc4c8e327a8373e"
    assert len(module.SCENARIO_IDS) == 32
    assert len(set(module.SCENARIO_IDS)) == 32
    assert module.SCENARIO_IDS[-1] == "final_rc1_publication_authorization_readiness"
    assert len(module.ASSET_PATHS) == 24
    assert len({Path(path).name for path in module.ASSET_PATHS}) == 24


def test_aion_244_report_when_committed_is_pass_fingerprinted_and_zero_effect() -> None:
    if not REPORT_PATH.is_file():
        return

    module = load_evaluator()
    payload = json.loads(REPORT_PATH.read_text(encoding="utf-8"))

    module.validate_report(payload)
    assert payload["decision"] == module.PASS_DECISION
    assert payload["evaluation_passed"] is True
    assert payload["candidate_rebuilds_executed_by_evaluation"] == 0
    assert payload["tags_created_by_evaluation"] == 0
    assert payload["github_releases_created_by_evaluation"] == 0
    assert payload["release_assets_uploaded_by_evaluation"] == 0
    assert payload["production_deployments"] == 0
