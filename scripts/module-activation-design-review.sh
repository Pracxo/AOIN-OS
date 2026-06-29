#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

required_docs=(
  docs/modules/module-activation-design-review.md
  docs/modules/plugin-boundary-evidence-pack.md
  docs/modules/module-activation-pre-gate.md
  docs/modules/code-loading-disabled-proof.md
  docs/modules/runtime-registration-disabled-proof.md
  docs/modules/capability-activation-disabled-proof.md
  docs/modules/module-lifecycle-traceability-matrix.md
  docs/modules/future-activation-implementation-prerequisites.md
  docs/modules/module-activation-no-go-regression-pack.md
  docs/adr/0096-module-activation-design-review-gate.md
)

required_examples=(
  examples/modules/module-activation-design-review.json
  examples/modules/plugin-boundary-evidence-pack.json
  examples/modules/module-activation-pre-gate-result.json
  examples/modules/module-lifecycle-traceability-matrix.json
  examples/modules/module-activation-no-go-regression-result.json
)

for file in "${required_docs[@]}"; do
  test -f "$file" || {
    echo "missing module activation review doc: $file" >&2
    exit 1
  }
done

for file in "${required_examples[@]}"; do
  test -f "$file" || {
    echo "missing module activation review example: $file" >&2
    exit 1
  }
done

test -x scripts/module-activation-no-go-regression.sh || {
  echo "module-activation-no-go-regression.sh must be executable" >&2
  exit 1
}

grep -q "0096-module-activation-design-review-gate.md" docs/adr/README.md || {
  echo "ADR 0096 is not indexed" >&2
  exit 1
}

./scripts/module-pack-check.sh
./scripts/generic-knowledge-demo.sh --offline-ok --skip-api
./scripts/module-lifecycle-dashboard-check.sh
./scripts/operator-platform-freeze-gate.sh
./scripts/ui-release-gate.sh
./scripts/docs-check.sh
./scripts/final-docs-audit.sh
./scripts/verify-no-domain-drift.sh
./scripts/boundary-check.sh
./scripts/module-activation-no-go-regression.sh

if git diff --name-only --diff-filter=ACMRT HEAD -- infra/postgres/migrations services/brain-api/migrations | rg -n '.'; then
  echo "AION-105 must not add or change migrations" >&2
  exit 1
fi

if git ls-files --others --exclude-standard infra/postgres/migrations services/brain-api/migrations | rg -n '.'; then
  echo "AION-105 must not add untracked migrations" >&2
  exit 1
fi

if git diff --name-only --diff-filter=ACMRT HEAD -- services/brain-api/src/aion_brain/api | rg -n '.'; then
  echo "AION-105 must not change API router files" >&2
  exit 1
fi

if git ls-files --others --exclude-standard services/brain-api/src/aion_brain/api | rg -n '.'; then
  echo "AION-105 must not add API router files" >&2
  exit 1
fi

for file in \
  package.json \
  package-lock.json \
  pnpm-lock.yaml \
  yarn.lock \
  bun.lockb; do
  if find . -path './.git' -prune -o -type f -name "$file" -print | rg -n '.'; then
    echo "package manager file is not allowed for AION-105: $file" >&2
    exit 1
  fi
done

if rg -n 'https?://' "${required_docs[@]}" "${required_examples[@]}"; then
  echo "external URL found in module activation review artifacts" >&2
  exit 1
fi

if rg -n 'npm[[:space:]]+install|pnpm[[:space:]]+install|yarn[[:space:]]+add|bun[[:space:]]+add|pip[[:space:]]+install' \
  "${required_docs[@]}" "${required_examples[@]}"; then
  echo "package install instruction found in module activation review artifacts" >&2
  exit 1
fi

python3 - "$ROOT_DIR" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

root = Path(sys.argv[1])
example_dir = root / "examples/modules"

design = json.loads((example_dir / "module-activation-design-review.json").read_text())
if design.get("status") != "passed":
    raise SystemExit("module activation design review status must be passed")
for key in (
    "activation_enabled",
    "code_loading_enabled",
    "runtime_registration_enabled",
    "capability_activation_enabled",
    "controlled_execution_enabled",
    "package_installation_enabled",
    "external_calls_enabled",
    "module_writes_enabled",
):
    if design.get(key) is not False:
        raise SystemExit(f"{key} must be false in module activation design review")

pre_gate = json.loads((example_dir / "module-activation-pre-gate-result.json").read_text())
if pre_gate.get("status") != "passed":
    raise SystemExit("module activation pre-gate result status must be passed")
for key in (
    "activation_enabled",
    "code_loading_enabled",
    "runtime_registration_enabled",
    "capability_activation_enabled",
    "controlled_execution_enabled",
    "package_installation_enabled",
    "external_dependency_download_enabled",
    "executable_payload_accepted",
    "policy_bypass_enabled",
    "audit_bypass_enabled",
    "module_writes_enabled",
    "activation_ready_default",
):
    if pre_gate.get(key) is not False:
        raise SystemExit(f"{key} must be false in module activation pre-gate result")

plugin = json.loads((example_dir / "plugin-boundary-evidence-pack.json").read_text())
if plugin.get("status") != "passed":
    raise SystemExit("plugin boundary evidence status must be passed")
if plugin.get("payload_executable") is not False:
    raise SystemExit("plugin boundary evidence must keep payload_executable=false")
areas = {row.get("area") for row in plugin.get("evidence", [])}
for area in {
    "extension manifest validation",
    "extension intake",
    "module slot",
    "capability binding",
    "binding validation",
    "conformance",
    "readiness",
    "activation request",
    "activation gate",
    "runtime registration preview",
    "module mock runtime",
    "operator review",
    "release and freeze checks",
    "boundary checks",
}:
    if area not in areas:
        raise SystemExit(f"plugin boundary evidence missing {area}")
for row in plugin.get("evidence", []):
    if row.get("expected_status") != "passed":
        raise SystemExit(f"plugin evidence row must expect passed: {row}")
    if row.get("release_blocker") is not True:
        raise SystemExit(f"plugin evidence row must be release blocker: {row}")

trace = json.loads((example_dir / "module-lifecycle-traceability-matrix.json").read_text())
if trace.get("status") != "passed":
    raise SystemExit("module lifecycle traceability matrix status must be passed")
for row in trace.get("rows", []):
    if row.get("activation_allowed") is not False:
        raise SystemExit(f"traceability row must keep activation_allowed=false: {row}")

no_go = json.loads((example_dir / "module-activation-no-go-regression-result.json").read_text())
if no_go.get("status") != "passed":
    raise SystemExit("module activation no-go regression status must be passed")
for row in no_go.get("checks", []):
    if row.get("expected_status") != "passed" or row.get("present") is not False:
        raise SystemExit(f"no-go regression row must be passed and absent: {row}")

serialized = json.dumps([design, pre_gate, plugin, trace, no_go], sort_keys=True).lower()
for marker in (
    "sk-",
    "ghp_",
    "xoxb-",
    "-----begin private key-----",
    "bearer ",
    "basic ",
    "api_key",
    "private_key",
    "raw_prompt",
    "hidden_reasoning",
    "chain_of_thought",
):
    if marker in serialized:
        raise SystemExit(f"blocked sensitive marker found in module activation examples: {marker}")

print("Module activation design review JSON checks PASS")
PY

echo "Module activation design review result:"
echo "- module_pack: passed"
echo "- generic_knowledge_demo: passed"
echo "- module_lifecycle_dashboard: passed"
echo "- operator_platform_freeze_gate: passed"
echo "- ui_release_gate: passed"
echo "- docs_and_boundary: passed"
echo "- no_go_regression: passed"
echo "Module activation design review PASS"
