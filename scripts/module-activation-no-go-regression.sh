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

for file in "${required_docs[@]}" "${required_examples[@]}"; do
  test -f "$file" || {
    echo "missing AION-105 module activation review artifact: $file" >&2
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
    echo "package manager file is not allowed for AION-105: $file" >&2
    exit 1
  fi
done

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

if git diff --name-only --diff-filter=ACMRT HEAD -- packages/aion-sdk-python/src/aion_sdk/resources packages/aion-sdk-python/src/aion_sdk/cli.py packages/aion-sdk-python/src/aion_sdk/cli | rg -n '.'; then
  echo "AION-105 must not add SDK resources or CLI command implementations" >&2
  exit 1
fi

if git ls-files --others --exclude-standard packages/aion-sdk-python/src/aion_sdk/resources packages/aion-sdk-python/src/aion_sdk/cli.py packages/aion-sdk-python/src/aion_sdk/cli | rg -n '.'; then
  echo "AION-105 must not add untracked SDK resources or CLI command implementations" >&2
  exit 1
fi

if rg -n 'https?://' "${required_docs[@]}" "${required_examples[@]}"; then
  echo "external URL found in AION-105 module activation artifacts" >&2
  exit 1
fi

if rg -n 'npm[[:space:]]+install|pnpm[[:space:]]+install|yarn[[:space:]]+add|bun[[:space:]]+add|pip[[:space:]]+install' \
  "${required_docs[@]}" "${required_examples[@]}"; then
  echo "package install instruction found in AION-105 artifacts" >&2
  exit 1
fi

python3 - "$ROOT_DIR" <<'PY'
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

root = Path(sys.argv[1])

required_docs = [
    Path("docs/modules/module-activation-design-review.md"),
    Path("docs/modules/plugin-boundary-evidence-pack.md"),
    Path("docs/modules/module-activation-pre-gate.md"),
    Path("docs/modules/code-loading-disabled-proof.md"),
    Path("docs/modules/runtime-registration-disabled-proof.md"),
    Path("docs/modules/capability-activation-disabled-proof.md"),
    Path("docs/modules/module-lifecycle-traceability-matrix.md"),
    Path("docs/modules/future-activation-implementation-prerequisites.md"),
    Path("docs/modules/module-activation-no-go-regression-pack.md"),
    Path("docs/adr/0096-module-activation-design-review-gate.md"),
]
required_examples = [
    Path("examples/modules/module-activation-design-review.json"),
    Path("examples/modules/plugin-boundary-evidence-pack.json"),
    Path("examples/modules/module-activation-pre-gate-result.json"),
    Path("examples/modules/module-lifecycle-traceability-matrix.json"),
    Path("examples/modules/module-activation-no-go-regression-result.json"),
]


def run_git(args: list[str]) -> list[str]:
    completed = subprocess.run(
        ["git", *args],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    return [line.strip() for line in completed.stdout.splitlines() if line.strip()]


changed = set(run_git(["diff", "--name-only", "--diff-filter=ACMRT", "HEAD", "--"]))
changed.update(run_git(["ls-files", "--others", "--exclude-standard"]))

runtime_prefixes = (
    "services/brain-api/src/",
    "packages/aion-sdk-python/src/",
    "operator-console-static/",
)
allowed_review_prefixes = (
    "docs/",
    "examples/",
    "services/brain-api/tests/",
)
allowed_review_files = {
    "scripts/module-activation-design-review.sh",
    "scripts/module-activation-no-go-regression.sh",
}

runtime_patterns = {
    "code loader": re.compile(r"\b(plugin|extension|module)[_\-\s]*(code[_\-\s]*)?loader\b", re.I),
    "package installer": re.compile(r"\b(package|dependency)[_\-\s]*installer\b", re.I),
    "dynamic module import": re.compile(r"\b(importlib\.import_module|__import__\s*\(|dynamic[_\-\s]*import)\b", re.I),
    "dynamic route registration": re.compile(r"\b(add_api_route|include_router|dynamic[_\-\s]*(api[_\-\s]*)?route[_\-\s]*registration)\b", re.I),
    "activation default true": re.compile(r"\bactivation_ready\s*[:=]\s*true\b|\bactivation_enabled\s*[:=]\s*true\b", re.I),
    "capability activation": re.compile(r"\bcapability_activation_enabled\s*[:=]\s*true\b|\bactivate_capabilit", re.I),
    "controlled execution": re.compile(r"\bcontrolled_execution_enabled\s*[:=]\s*true\b|\bcontrolled_supported\s*[:=]\s*true\b", re.I),
    "executable payload": re.compile(r"\bexecutable_payload\s*[:=]\s*true\b|\bpayload_executable\s*[:=]\s*true\b", re.I),
    "module writes": re.compile(r"\bmodule_writes_enabled\s*[:=]\s*true\b|\bwrite_allowed\s*[:=]\s*true\b", re.I),
    "policy bypass": re.compile(r"\bpolicy_bypass(_enabled)?\s*[:=]\s*true\b", re.I),
    "audit bypass": re.compile(r"\baudit_bypass(_enabled)?\s*[:=]\s*true\b", re.I),
    "external dependency download": re.compile(r"\b(external_dependency_download_enabled|dependency_download_enabled)\s*[:=]\s*true\b", re.I),
}

for relative in sorted(changed):
    path = root / relative
    if not path.is_file():
        continue
    if relative in allowed_review_files or relative.startswith(allowed_review_prefixes):
        continue
    if not relative.startswith(runtime_prefixes):
        continue
    text = path.read_text(errors="ignore")
    if relative == "operator-console-static/app.js":
        text = text.replace(
            '{ action_key: "activate_capability", reason: "Disabled in static prototype." }',
            "",
        )
    if relative in {
        "operator-console-static/demo-data/platform-integration-checkpoint.json",
        "operator-console-static/demo-data/future-runtime-boundary-freeze.json",
    }:
        text = re.sub(
            r'\{\s*"action_key":\s*"activate_capability",\s*"reason":\s*"Disabled (?:in the platform checkpoint|by the future runtime boundary freeze)\."\s*\}',
            "",
            text,
        )
    for label, pattern in runtime_patterns.items():
        if pattern.search(text):
            raise SystemExit(f"runtime implementation pattern found in {relative}: {label}")

for doc in required_docs:
    text = (root / doc).read_text().lower()
    if not any(marker in text for marker in ("disabled", "no-go", "preview", "synthetic", "blocked")):
        raise SystemExit(f"AION-105 doc must state disabled/no-go/preview/synthetic posture: {doc}")

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
    "raw_prompt",
    "hidden_reasoning",
    "chain_of_thought",
):
    if marker in serialized:
        raise SystemExit(f"blocked sensitive marker found in AION-105 examples: {marker}")

dangerous_false_keys = {
    "activation_enabled",
    "code_loading_enabled",
    "runtime_registration_enabled",
    "capability_activation_enabled",
    "controlled_execution_enabled",
    "package_installation_enabled",
    "external_calls_enabled",
    "external_dependency_download_enabled",
    "executable_payload_accepted",
    "policy_bypass_enabled",
    "audit_bypass_enabled",
    "module_writes_enabled",
    "activation_ready_default",
}


def assert_false_keys(value: object, context: str) -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            if key in dangerous_false_keys and nested is not False:
                raise SystemExit(f"{context}.{key} must be false")
            assert_false_keys(nested, f"{context}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            assert_false_keys(item, f"{context}[{index}]")


for name, payload in examples.items():
    assert_false_keys(payload, name)

no_go = examples["module-activation-no-go-regression-result.json"]
if no_go.get("status") != "passed":
    raise SystemExit("module activation no-go regression result must be passed")
for item in no_go.get("checks", []):
    if item.get("expected_status") != "passed" or item.get("present") is not False:
        raise SystemExit(f"no-go check must be passed and absent: {item}")

trace = examples["module-lifecycle-traceability-matrix.json"]
required_stages = {
    "manifest",
    "intake",
    "slot",
    "binding",
    "validation",
    "conformance",
    "readiness",
    "activation request",
    "activation gate",
    "blockers",
    "registration preview",
    "mock runtime",
    "operator review",
    "audit/provenance",
    "evidence script",
}
stages = {row.get("stage") for row in trace.get("rows", [])}
missing = required_stages - stages
if missing:
    raise SystemExit(f"traceability matrix missing stages: {sorted(missing)}")
for row in trace.get("rows", []):
    if row.get("activation_allowed") is not False:
        raise SystemExit(f"traceability row must keep activation_allowed=false: {row}")

plugin = examples["plugin-boundary-evidence-pack.json"]
if plugin.get("status") != "passed":
    raise SystemExit("plugin boundary evidence status must be passed")
if plugin.get("payload_executable") is not False:
    raise SystemExit("plugin boundary evidence payload_executable must be false")
required_areas = {
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
}
areas = {row.get("area") for row in plugin.get("evidence", [])}
missing_areas = required_areas - areas
if missing_areas:
    raise SystemExit(f"plugin evidence missing areas: {sorted(missing_areas)}")
for row in plugin.get("evidence", []):
    if row.get("expected_status") != "passed":
        raise SystemExit(f"plugin evidence row must expect passed: {row}")
    if row.get("release_blocker") is not True:
        raise SystemExit(f"plugin evidence row must be release blocker: {row}")
    if not str(row.get("script", "")).startswith("./scripts/"):
        raise SystemExit(f"plugin evidence row must use local script: {row}")

print("AION-105 module activation no-go JSON and changed-file checks PASS")
PY

echo "Module activation no-go regression result:"
echo "- code_loading: disabled"
echo "- package_installation: disabled"
echo "- runtime_registration: disabled"
echo "- capability_activation: disabled"
echo "- controlled_execution: disabled"
echo "- module_writes: disabled"
echo "Module activation no-go regression PASS"
