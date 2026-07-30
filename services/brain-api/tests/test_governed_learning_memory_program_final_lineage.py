from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
HARNESS = REPO_ROOT / "scripts/lib/governed_learning_memory_program_final_evaluation.py"


def _load_harness():
    spec = importlib.util.spec_from_file_location("aion229_lineage", HARNESS)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_final_evaluation_verifies_aion227_and_aion228_delivery_lineage() -> None:
    harness = _load_harness()
    aion227 = harness.validate_aion227_delivery(REPO_ROOT)
    aion228 = harness.validate_aion228_delivery(REPO_ROOT)
    authorization = harness.validate_authorization_and_ledgers(REPO_ROOT)
    assert aion227["primary_pr"] == 144
    assert aion227["corrective_pr"] == 143
    assert aion228["pull_request"] == 145
    assert aion228["feature_commit"] == harness.AION228_FEATURE_COMMIT
    assert aion228["merge_commit"] == harness.AION228_MERGE_COMMIT
    assert authorization["authorization_transaction_id"] == "AION-227-GLM-0004"
