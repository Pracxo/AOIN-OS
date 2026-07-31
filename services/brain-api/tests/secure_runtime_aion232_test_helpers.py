from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
REPORT_PATH = (
    REPO_ROOT
    / "examples/secure-runtime-integration/runtime-foundation-operator-evaluation-report.json"
)
PROGRAM_LEDGER_PATH = REPO_ROOT / "docs/secure-runtime-integration/program-ledger.json"
AUTH_LEDGER_PATH = REPO_ROOT / "docs/secure-runtime-integration/authorization-ledger.json"
PASS_DECISION = (
    "SECURE_LOCAL_OPERATOR_RUNTIME_OPERATOR_EVALUATION_PASS_RECOMMEND_"
    "CONTROLLED_MODEL_GATEWAY_AUTHORIZATION"
)
FAIL_DECISION = (
    "SECURE_LOCAL_OPERATOR_RUNTIME_OPERATOR_EVALUATION_FAIL_REMAIN_LOCAL_SIMULATION_ONLY"
)
AION230 = "AION-230-SRI-0001"
AION232 = "AION-232-SRI-0002"
AION231_FEATURE = "45540009d03f60d7477330a88946e73705ee60e5"
AION231_MERGE = "8bb9af29cc2cf960d9efdfe2ee323d7245812747"
AION231_MERGED_AT = "2026-07-30T19:45:59Z"
MODEL_GATEWAY_SCOPE = (
    "authenticated-local-model-request-envelope-provider-model-manifest-closed-allowlist-"
    "context-token-budget-redaction-routing-fallback-retry-circuit-breaker-cost-latency-"
    "estimation-structured-output-validation-untrusted-output-provenance-deterministic-"
    "reference-provider-no-egress-core"
)


def load_json(relative: str | Path) -> dict[str, Any]:
    path = relative if isinstance(relative, Path) else REPO_ROOT / relative
    return json.loads(Path(path).read_text(encoding="utf-8"))


def report() -> dict[str, Any]:
    return load_json(REPORT_PATH)


def program() -> dict[str, Any]:
    return load_json(PROGRAM_LEDGER_PATH)


def authorization() -> dict[str, Any]:
    return load_json(AUTH_LEDGER_PATH)


def scenario(scenario_id: str) -> dict[str, Any]:
    for item in report()["scenario_results"]:
        if item["scenario_id"] == scenario_id:
            return item
    raise AssertionError(f"missing scenario {scenario_id}")


def active_authorization_record() -> dict[str, Any]:
    for item in authorization()["records"]:
        if item["authorization_transaction_id"] == AION232:
            return item
    raise AssertionError("missing AION-232 authorization record")


def closed_aion230_record() -> dict[str, Any]:
    for item in authorization()["records"]:
        if item["authorization_transaction_id"] == AION230:
            return item
    raise AssertionError("missing AION-230 authorization record")


def changed_paths_since_main() -> set[str]:
    def run(args: list[str]) -> subprocess.CompletedProcess[str]:
        return subprocess.run(args, cwd=REPO_ROOT, text=True, capture_output=True, check=False)

    changed: set[str] = set()
    for candidate in ("origin/main", "main"):
        if run(["git", "rev-parse", "--verify", "--quiet", candidate]).returncode != 0:
            continue
        merge_base = run(["git", "merge-base", "HEAD", candidate])
        if merge_base.returncode == 0 and merge_base.stdout.strip():
            diff = run(["git", "diff", "--name-only", merge_base.stdout.strip(), "HEAD"])
            changed.update(line.strip() for line in diff.stdout.splitlines() if line.strip())
            break
    for args in (["git", "diff", "--name-only"], ["git", "diff", "--cached", "--name-only"]):
        result = run(args)
        changed.update(line.strip() for line in result.stdout.splitlines() if line.strip())
    for line in run(
        ["git", "status", "--porcelain=v1", "--untracked-files=all"]
    ).stdout.splitlines():
        if line.startswith("?? "):
            changed.add(line[3:])
    return changed
