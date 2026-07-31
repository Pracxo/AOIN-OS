from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
HARNESS = REPO_ROOT / "scripts/lib/model_gateway_operator_evaluation.py"


def load_harness():
    spec = importlib.util.spec_from_file_location("aion234_eval_test", HARNESS)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def load_json(relative: str):
    return json.loads((REPO_ROOT / relative).read_text(encoding="utf-8"))


def scenario(report, scenario_id: str):
    return next(item for item in report["scenario_results"] if item["scenario_id"] == scenario_id)


def report():
    return load_json(
        "examples/secure-runtime-integration/model-gateway-operator-evaluation-report.json"
    )


def capability_auth():
    return load_json("examples/secure-runtime-integration/capability-runtime-authorization.json")
