from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
HARNESS = REPO_ROOT / "scripts/lib/governed_learning_memory_program_final_evaluation.py"
LIVE_EVIDENCE = (
    REPO_ROOT
    / "examples/governed-learning-memory/controlled-local-continual-learning-live-pilot-evidence.json"
)


def _load_harness():
    spec = importlib.util.spec_from_file_location("aion229_live_evidence", HARNESS)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_final_evaluation_validates_committed_live_pilot_evidence() -> None:
    harness = _load_harness()
    payload = json.loads(LIVE_EVIDENCE.read_text(encoding="utf-8"))
    validated = harness.validate_live_evidence(payload, repo_root=REPO_ROOT)
    assert validated["pilot_id"] == "AION-228-controlled-local-continual-learning-live-pilot"
    assert validated["report_fingerprint"] == harness.AION228_REPORT_FINGERPRINT
    assert validated["cycle_count"] == 3
    assert validated["cycle_outcomes"] == ["completed", "completed", "abstained"]
    assert validated["source_bodies_retained"] == 0
    assert validated["stage_receipt_count"] == 33
    assert validated["checkpoint_count"] == 3
    assert validated["protected_material_absent"] is True


def test_live_evidence_rejects_fingerprint_or_protected_material_drift() -> None:
    harness = _load_harness()
    payload = json.loads(LIVE_EVIDENCE.read_text(encoding="utf-8"))
    bad_fingerprint = json.loads(json.dumps(payload))
    bad_fingerprint["report_fingerprint"] = "0" * 64
    try:
        harness.validate_live_evidence(bad_fingerprint, repo_root=REPO_ROOT)
    except ValueError as exc:
        assert "live evidence mismatch" in str(exc) or "fingerprint" in str(exc)
    else:
        raise AssertionError("invalid live-evidence fingerprint accepted")

    protected = json.loads(json.dumps(payload))
    protected["raw_source_body"] = "raw source body"
    try:
        harness.validate_live_evidence(protected, repo_root=REPO_ROOT)
    except ValueError as exc:
        assert "protected" in str(exc)
    else:
        raise AssertionError("protected live evidence accepted")
