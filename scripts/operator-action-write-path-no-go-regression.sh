#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/portable-search.sh"

required_docs=(
  docs/operator-actions/write-path-architecture.md
  docs/operator-actions/approval-boundary-design.md
  docs/operator-actions/execution-boundary-design.md
  docs/operator-actions/action-intent-lifecycle.md
  docs/operator-actions/controlled-execution-prerequisites.md
  docs/operator-actions/rollback-and-undo-model.md
  docs/operator-actions/separation-of-duties.md
  docs/operator-actions/write-path-threat-model.md
  docs/operator-actions/write-path-release-gates.md
  docs/operator-actions/write-path-no-go-regression-pack.md
  docs/adr/0098-operator-action-write-path-architecture.md
)

required_examples=(
  examples/operator-actions/write-path-architecture.json
  examples/operator-actions/action-intent-lifecycle.json
  examples/operator-actions/write-path-release-gates.json
  examples/operator-actions/write-path-no-go-regression-result.json
)

for file in "${required_docs[@]}" "${required_examples[@]}"; do
  test -f "$file" || {
    echo "missing AION-107 write-path artifact: $file" >&2
    exit 1
  }
done

for file in \
  package.json \
  package-lock.json \
  pnpm-lock.yaml \
  yarn.lock \
  bun.lockb; do
  if find . -path './.git' -prune -o -type f -name "$file" -print | rg -n '.'; then
    echo "package manager file is not allowed for AION-107: $file" >&2
    exit 1
  fi
done

if git diff --name-only --diff-filter=ACMRT HEAD -- infra/postgres/migrations services/brain-api/migrations | rg -n '.'; then
  echo "AION-107 must not add or change migrations" >&2
  exit 1
fi

if git ls-files --others --exclude-standard infra/postgres/migrations services/brain-api/migrations | rg -n '.'; then
  echo "AION-107 must not add untracked migrations" >&2
  exit 1
fi

if git diff --name-only --diff-filter=ACMRT HEAD -- services/brain-api/src/aion_brain/api \
  | rg -v '^services/brain-api/src/aion_brain/api/connector_runtime\.py$|^services/brain-api/src/aion_brain/api/connector_simulator\.py$' \
  | rg -n '.'; then
  echo "AION-107 must not change API router files" >&2
  exit 1
fi

if git ls-files --others --exclude-standard services/brain-api/src/aion_brain/api \
  | rg -v '^services/brain-api/src/aion_brain/api/connector_runtime\.py$|^services/brain-api/src/aion_brain/api/connector_simulator\.py$' \
  | rg -n '.'; then
  echo "AION-107 must not add API router files" >&2
  exit 1
fi

if git diff --name-only --diff-filter=ACMRT HEAD -- packages/aion-sdk-python/src/aion_sdk/resources packages/aion-sdk-python/src/aion_sdk/cli.py packages/aion-sdk-python/src/aion_sdk/cli \
  | rg -v '^packages/aion-sdk-python/src/aion_sdk/resources/connector_runtime\.py$|^packages/aion-sdk-python/src/aion_sdk/resources/connector_simulator\.py$|^packages/aion-sdk-python/src/aion_sdk/cli/commands/connector_runtime\.py$|^packages/aion-sdk-python/src/aion_sdk/cli/commands/connector_simulator\.py$|^packages/aion-sdk-python/src/aion_sdk/cli/main\.py$' \
  | rg -n '.'; then
  echo "AION-107 must not add SDK resources or CLI command implementations" >&2
  exit 1
fi

if git ls-files --others --exclude-standard packages/aion-sdk-python/src/aion_sdk/resources packages/aion-sdk-python/src/aion_sdk/cli.py packages/aion-sdk-python/src/aion_sdk/cli \
  | rg -v '^packages/aion-sdk-python/src/aion_sdk/resources/connector_runtime\.py$|^packages/aion-sdk-python/src/aion_sdk/resources/connector_simulator\.py$|^packages/aion-sdk-python/src/aion_sdk/cli/commands/connector_runtime\.py$|^packages/aion-sdk-python/src/aion_sdk/cli/commands/connector_simulator\.py$|^packages/aion-sdk-python/src/aion_sdk/cli/main\.py$' \
  | rg -n '.'; then
  echo "AION-107 must not add untracked SDK resources or CLI command implementations" >&2
  exit 1
fi

if rg -n 'https?://' "${required_docs[@]}" "${required_examples[@]}"; then
  echo "external URL or endpoint found in AION-107 artifacts" >&2
  exit 1
fi

if rg -n 'npm[[:space:]]+install|pnpm[[:space:]]+install|yarn[[:space:]]+add|bun[[:space:]]+add|pip[[:space:]]+install' \
  "${required_docs[@]}" "${required_examples[@]}"; then
  echo "package install instruction found in AION-107 artifacts" >&2
  exit 1
fi

python3 - "$ROOT_DIR" <<'PY'
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

root = Path(sys.argv[1])

required_docs = [
    Path("docs/operator-actions/write-path-architecture.md"),
    Path("docs/operator-actions/approval-boundary-design.md"),
    Path("docs/operator-actions/execution-boundary-design.md"),
    Path("docs/operator-actions/action-intent-lifecycle.md"),
    Path("docs/operator-actions/controlled-execution-prerequisites.md"),
    Path("docs/operator-actions/rollback-and-undo-model.md"),
    Path("docs/operator-actions/separation-of-duties.md"),
    Path("docs/operator-actions/write-path-threat-model.md"),
    Path("docs/operator-actions/write-path-release-gates.md"),
    Path("docs/operator-actions/write-path-no-go-regression-pack.md"),
    Path("docs/adr/0098-operator-action-write-path-architecture.md"),
]
required_examples = [
    Path("examples/operator-actions/write-path-architecture.json"),
    Path("examples/operator-actions/action-intent-lifecycle.json"),
    Path("examples/operator-actions/write-path-release-gates.json"),
    Path("examples/operator-actions/write-path-no-go-regression-result.json"),
]


def run_git(args: list[str], check: bool = True) -> list[str]:
    completed = subprocess.run(
        ["git", *args],
        cwd=root,
        check=check,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        return []
    return [line.strip() for line in completed.stdout.splitlines() if line.strip()]


def ref_exists(ref: str) -> bool:
    completed = subprocess.run(
        ["git", "rev-parse", "--verify", "--quiet", ref],
        cwd=root,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return completed.returncode == 0


def comparison_base() -> str | None:
    candidates: list[str] = []
    github_base_ref = os.environ.get("GITHUB_BASE_REF")
    if github_base_ref:
        candidates.extend([f"origin/{github_base_ref}", github_base_ref])
    candidates.extend(["origin/main", "main"])
    for candidate in candidates:
        if not ref_exists(candidate):
            continue
        merge_base = subprocess.run(
            ["git", "merge-base", "HEAD", candidate],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )
        if merge_base.returncode == 0 and merge_base.stdout.strip():
            return merge_base.stdout.strip()
    if ref_exists("HEAD~1"):
        return "HEAD~1"
    return None


changed: set[str] = set()
base = comparison_base()
if base is not None:
    changed.update(run_git(["diff", "--name-only", "--diff-filter=ACMRT", base, "HEAD"], check=False))
changed.update(run_git(["diff", "--name-only", "--diff-filter=ACMRT"], check=False))
changed.update(run_git(["diff", "--name-only", "--cached", "--diff-filter=ACMRT"], check=False))
changed.update(run_git(["ls-files", "--others", "--exclude-standard"], check=False))

allowed_review_prefixes = (
    "docs/",
    "examples/",
    "services/brain-api/tests/",
)
allowed_review_files = {
    "scripts/operator-action-write-path-design-check.sh",
    "scripts/operator-action-write-path-no-go-regression.sh",
    "scripts/connector-runtime-check.sh",
    "scripts/connector-boundary-design-check.sh",
    "scripts/connector-no-go-regression.sh",
}
allowed_aion108_prefixes = (
    "services/brain-api/src/aion_brain/connector_runtime/",
)
allowed_aion110_prefixes = (
    "services/brain-api/src/aion_brain/connector_simulator/",
)
allowed_aion108_files = {
    ".env.example",
    "AGENTS.md",
    "README.md",
    "operator-console-static/README.md",
    "operator-console-static/app.js",
    "operator-console-static/index.html",
    "operator-console-static/styles.css",
    "operator-console-static/demo-data/connector-boundary-preview.json",
    "operator-console-static/demo-data/connector-runtime-status.json",
    "packages/aion-sdk-python/src/aion_sdk/client.py",
    "packages/aion-sdk-python/src/aion_sdk/cli/main.py",
    "packages/aion-sdk-python/src/aion_sdk/cli/commands/connector_runtime.py",
    "packages/aion-sdk-python/src/aion_sdk/resources/connector_runtime.py",
    "packages/aion-sdk-python/tests/test_cli_connector_runtime.py",
    "packages/aion-sdk-python/tests/test_connector_runtime_resource.py",
    "services/brain-api/src/aion_brain/api/connector_runtime.py",
    "services/brain-api/src/aion_brain/audit_integrity/ledger.py",
    "services/brain-api/src/aion_brain/audit_integrity/provenance.py",
    "services/brain-api/src/aion_brain/config.py",
    "services/brain-api/src/aion_brain/contracts/connector_runtime.py",
    "services/brain-api/src/aion_brain/contracts/telemetry.py",
    "services/brain-api/src/aion_brain/freeze/gate.py",
    "services/brain-api/src/aion_brain/kernel/app_factory.py",
    "services/brain-api/src/aion_brain/kernel/container.py",
    "services/brain-api/src/aion_brain/kernel/diagnostics.py",
    "services/brain-api/src/aion_brain/main.py",
    "services/brain-api/src/aion_brain/policy_catalog/defaults.py",
    "services/brain-api/src/aion_brain/release_package/packager.py",
    "services/brain-api/src/aion_brain/security_baseline/hardening_gate.py",
    "services/brain-api/src/aion_brain/telemetry/visual.py",
}
allowed_aion110_files = {
    "operator-console-static/demo-data/connector-policy-readiness.json",
    "operator-console-static/demo-data/connector-simulation-preview.json",
    "packages/aion-sdk-python/src/aion_sdk/cli/commands/connector_simulator.py",
    "packages/aion-sdk-python/src/aion_sdk/resources/connector_simulator.py",
    "packages/aion-sdk-python/tests/test_cli_connector_simulator.py",
    "packages/aion-sdk-python/tests/test_connector_simulator_resource.py",
    "services/brain-api/src/aion_brain/api/connector_simulator.py",
    "services/brain-api/src/aion_brain/contracts/connector_simulator.py",
}
runtime_prefixes = (
    "services/brain-api/src/",
    "packages/aion-sdk-python/src/",
    "operator-console-static/",
    "infra/",
)

runtime_patterns = {
    "write execution path": re.compile(r"\b(write[_\-\s]*execution|execute[_\-\s]*write|run[_\-\s]*write[_\-\s]*action)\b", re.I),
    "tool execution path": re.compile(r"\b(tool[_\-\s]*execution|execute[_\-\s]*tool|tool_runner|run_tool)\b", re.I),
    "controlled handoff execution": re.compile(r"\b(controlled[_\-\s]*handoff[_\-\s]*execution|execute[_\-\s]*handoff)\b", re.I),
    "external call execution": re.compile(r"\b(requests\.(get|post|put|patch|delete)|httpx\.(get|post|put|patch|delete)|aiohttp\.ClientSession|urllib\.request)\b", re.I),
    "model generated tool execution": re.compile(r"\b(model[_\-\s]*generated[_\-\s]*(tool[_\-\s]*)?execution|llm[_\-\s]*tool[_\-\s]*execution)\b", re.I),
    "activation enablement": re.compile(r"\b(module_activation_enabled|capability_activation_enabled|activation_enabled)\s*[:=]\s*true\b", re.I),
    "hard delete enablement": re.compile(r"\b(hard_delete_enabled\s*[:=]\s*true|hard[_\-\s]*delete)\b", re.I),
    "approval bypass": re.compile(r"\bapproval_bypass(_enabled)?\s*[:=]\s*true\b|\bbypass[_\-\s]*approval\b", re.I),
    "policy bypass": re.compile(r"\bpolicy_bypass(_enabled)?\s*[:=]\s*true\b|\bbypass[_\-\s]*policy\b", re.I),
    "audit bypass": re.compile(r"\baudit_bypass(_enabled)?\s*[:=]\s*true\b|\bbypass[_\-\s]*audit\b", re.I),
}

for relative in sorted(changed):
    path = root / relative
    if not path.is_file():
        continue
    if (
        relative in allowed_review_files
        or relative in allowed_aion108_files
        or relative in allowed_aion110_files
        or relative.startswith(allowed_review_prefixes)
        or relative.startswith(allowed_aion108_prefixes)
        or relative.startswith(allowed_aion110_prefixes)
    ):
        continue
    if not relative.startswith(runtime_prefixes):
        continue
    text = path.read_text(errors="ignore")
    for label, pattern in runtime_patterns.items():
        if pattern.search(text):
            raise SystemExit(f"operator action write-path runtime pattern found in {relative}: {label}")

combined_docs = "\n".join((root / path).read_text().lower() for path in required_docs)
for marker in (
    "no write execution",
    "execution is future-only",
    "approval does not execute",
    "approval cannot bypass policy",
    "no direct tool execution",
    "no model-generated execution",
    "current lifecycle stops at previewed/reviewed/blocked",
    "future_execution_ready and future_executed are not reachable today",
):
    if marker not in combined_docs:
        raise SystemExit(f"AION-107 docs missing marker: {marker}")

threat_text = (root / "docs/operator-actions/write-path-threat-model.md").read_text().lower()
for threat in (
    "approval bypass",
    "policy bypass",
    "model-generated tool execution",
    "confused deputy",
    "replayed approval",
    "stale preview",
    "target drift",
    "irreversible action",
    "rollback failure",
    "audit tampering",
    "privilege escalation",
    "connector boundary bypass",
    "external call leakage",
):
    if threat not in threat_text:
        raise SystemExit(f"AION-107 threat model missing: {threat}")

examples = {path.name: json.loads((root / path).read_text()) for path in required_examples}
serialized = json.dumps(examples, sort_keys=True).lower()
for marker in (
    "sk-",
    "ghp_",
    "xoxb-",
    "-----begin private key-----",
    "bearer ",
    "basic ",
    "api_key",
    "private_key",
    "access_token",
    "refresh_token",
    "id_token",
    "client_secret",
    "raw_prompt",
    "hidden_reasoning",
    "chain_of_thought",
    "http://",
    "https://",
):
    if marker in serialized:
        raise SystemExit(f"blocked marker found in AION-107 examples: {marker}")

false_keys = {
    "execution_enabled",
    "external_calls_enabled",
    "activation_enabled",
    "write_execution_enabled",
    "tool_execution_enabled",
    "model_generated_execution_enabled",
    "controlled_handoff_execution_enabled",
    "connector_runtime_enabled",
    "production_auth_enabled",
    "policy_bypass_enabled",
    "audit_bypass_enabled",
    "approval_bypass_enabled",
    "hard_delete_enabled",
    "contains_secrets",
    "contains_credentials",
    "contains_tokens",
    "contains_external_endpoints",
    "contains_unredacted_prompts",
    "contains_private_reasoning",
}


def assert_false_keys(value: object, context: str) -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            if key in false_keys and nested is not False:
                raise SystemExit(f"{context}.{key} must be false")
            assert_false_keys(nested, f"{context}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            assert_false_keys(item, f"{context}[{index}]")


for name, payload in examples.items():
    if payload.get("status") != "passed":
        raise SystemExit(f"{name}.status must be passed")
    assert_false_keys(payload, name)

no_go = examples["write-path-no-go-regression-result.json"]
for item in no_go.get("checks", []):
    if item.get("expected_status") != "passed" or item.get("present") is not False:
        raise SystemExit(f"write-path no-go row must be passed and absent: {item}")

print("AION-107 operator action write-path no-go JSON and changed-file checks PASS")
PY

echo "Operator action write-path no-go regression result:"
echo "- write_execution: absent"
echo "- tool_execution: absent"
echo "- controlled_handoff_execution: absent"
echo "- external_calls: absent"
echo "- activation: absent"
echo "- hard_delete: absent"
echo "- approval_policy_audit_bypass: absent"
echo "Operator action write-path no-go regression PASS"
