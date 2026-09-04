from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

from aion243_release_candidate_scope import without_aion243_allowed_paths

REPO_ROOT = Path(__file__).resolve().parents[3]
AION248_SOURCE = {
    "services/brain-api/src/aion_brain/contracts/live_provider_pilot.py",
    "services/brain-api/src/aion_brain/live_provider_pilot/__init__.py",
    "services/brain-api/src/aion_brain/live_provider_pilot/authorization.py",
    "services/brain-api/src/aion_brain/live_provider_pilot/component_binding.py",
    "services/brain-api/src/aion_brain/live_provider_pilot/provider_selection.py",
    "services/brain-api/src/aion_brain/live_provider_pilot/operator_approval.py",
    "services/brain-api/src/aion_brain/live_provider_pilot/credential_boundary.py",
    "services/brain-api/src/aion_brain/live_provider_pilot/endpoint_policy.py",
    "services/brain-api/src/aion_brain/live_provider_pilot/request_projection.py",
    "services/brain-api/src/aion_brain/live_provider_pilot/response_projection.py",
    "services/brain-api/src/aion_brain/live_provider_pilot/usage_budget.py",
    "services/brain-api/src/aion_brain/live_provider_pilot/retention_policy.py",
    "services/brain-api/src/aion_brain/live_provider_pilot/transport.py",
    "services/brain-api/src/aion_brain/live_provider_pilot/openai_responses_adapter.py",
    "services/brain-api/src/aion_brain/live_provider_pilot/trust.py",
    "services/brain-api/src/aion_brain/live_provider_pilot/redaction.py",
    "services/brain-api/src/aion_brain/live_provider_pilot/replay.py",
    "services/brain-api/src/aion_brain/live_provider_pilot/audit.py",
    "services/brain-api/src/aion_brain/live_provider_pilot/observability.py",
    "services/brain-api/src/aion_brain/live_provider_pilot/integrity.py",
    "services/brain-api/src/aion_brain/live_provider_pilot/evidence.py",
}


def _aion239_source_paths() -> set[str]:
    program = json.loads(
        (REPO_ROOT / "docs/v02-release-qualification/program-ledger.json").read_text()
    )
    if (
        program.get("active_v02_release_qualification_task") not in {"AION-239", "AION-241"}
        or program.get("v02_release_qualification_foundation_implemented") is not True
        or program.get("foundation_runtime_state")
        != "implemented_disabled_design_only_local_simulation"
    ):
        return set()
    source_scope = program.get("implemented_source_scope")
    assert isinstance(source_scope, list)
    return {str(path) for path in source_scope}


def _aion248_source_paths() -> set[str]:
    adaptive = json.loads(
        (REPO_ROOT / "docs/adaptive-intelligence/program-ledger.json").read_text()
    )
    record = adaptive.get("aion_248_record", {})
    if (
        isinstance(record, dict)
        and adaptive.get("live_provider_pilot_authorized") is True
        and adaptive.get("active_adaptive_intelligence_authorization")
        == "AION-247-AI-0002"
        and adaptive.get("active_adaptive_intelligence_task") == "AION-248"
        and adaptive.get("formal_closeout_task") == "AION-249"
        and record.get("task_id") == "AION-248"
        and record.get("branch") == "phase/v03-openai-live-provider-pilot"
        and record.get("authorization_transaction") == "AION-247-AI-0002"
        and record.get("next_task") == "AION-249"
        and record.get("runtime_state")
        in {
            "single_openai_responses_api_live_provider_pilot_implementation_ready_live_execution_pending",
            "single_openai_responses_api_synthetic_live_provider_pilot_complete",
        }
    ):
        return set(AION248_SOURCE)
    return set()


def _assert_aion239_boundaries(paths: set[str]) -> None:
    changed = paths & _aion239_source_paths()
    if changed:
        assert changed <= _aion239_source_paths()
        assert not (
            REPO_ROOT
            / "services/brain-api/src/aion_brain/api/v02_release_qualification.py"
        ).exists()


def _assert_aion248_boundaries(paths: set[str]) -> None:
    changed = paths & _aion248_source_paths()
    if changed:
        assert changed <= _aion248_source_paths()
        assert not (
            REPO_ROOT / "services/brain-api/src/aion_brain/api/live_provider_pilot.py"
        ).exists()


def test_program_final_evaluation_no_go_script_passes() -> None:
    env = {**os.environ, "PYTEST_CURRENT_TEST": "AION-220 no-go"}
    script = (
        REPO_ROOT
        / "scripts/knowledge-intelligence-program-final-evaluation-no-go-regression.sh"
    )
    subprocess.run(
        [str(script)],
        cwd=REPO_ROOT,
        env=env,
        check=True,
    )


def test_program_final_evaluation_branch_does_not_modify_runtime_source() -> None:
    changed = subprocess.run(
        ["git", "diff", "--name-only", "origin/main...HEAD"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    paths = without_aion243_allowed_paths(
        {line.strip() for line in changed.stdout.splitlines() if line.strip()}
    )
    aion239_source_paths = _aion239_source_paths()
    aion248_source_paths = _aion248_source_paths()
    assert not {
        path
        for path in paths
        if path.startswith("services/brain-api/src/aion_brain/")
        and path not in aion239_source_paths
        and path not in aion248_source_paths
    }
    _assert_aion239_boundaries(paths)
    _assert_aion248_boundaries(paths)
    assert not {path for path in paths if path.startswith(".github/workflows/")}
