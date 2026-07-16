#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/portable-search.sh"

required_docs=(
  docs/connectors/external-connector-boundary-design.md
  docs/connectors/connector-trust-model.md
  docs/connectors/connector-credential-boundary.md
  docs/connectors/connector-egress-guard.md
  docs/connectors/connector-ingress-guard.md
  docs/connectors/connector-capability-declaration.md
  docs/connectors/connector-threat-model.md
  docs/connectors/connector-release-gates.md
  docs/connectors/connector-no-go-regression-pack.md
  docs/connectors/future-connector-implementation-prerequisites.md
  docs/adr/0097-external-connector-boundary-design.md
)

required_examples=(
  examples/connectors/connector-boundary-design.json
  examples/connectors/connector-trust-model.json
  examples/connectors/connector-threat-model.json
  examples/connectors/connector-release-gates.json
  examples/connectors/connector-no-go-regression-result.json
)

for file in "${required_docs[@]}" "${required_examples[@]}"; do
  test -f "$file" || {
    echo "missing AION-106 connector boundary artifact: $file" >&2
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
    echo "package manager file is not allowed for AION-106: $file" >&2
    exit 1
  fi
done

if git diff --name-only --diff-filter=ACMRT HEAD -- infra/postgres/migrations services/brain-api/migrations | rg -n '.'; then
  echo "AION-106 must not add or change migrations" >&2
  exit 1
fi

if git ls-files --others --exclude-standard infra/postgres/migrations services/brain-api/migrations | rg -n '.'; then
  echo "AION-106 must not add untracked migrations" >&2
  exit 1
fi

if git diff --name-only --diff-filter=ACMRT HEAD -- services/brain-api/src/aion_brain/api \
  | rg -v '^services/brain-api/src/aion_brain/api/connector_runtime\.py$|^services/brain-api/src/aion_brain/api/connector_simulator\.py$|^services/brain-api/src/aion_brain/api/connector_policy\.py$|^services/brain-api/src/aion_brain/api/connector_sandbox\.py$|^services/brain-api/src/aion_brain/api/connector_credentials\.py$' \
  | rg -n '.'; then
  echo "AION-106 must not change API router files" >&2
  exit 1
fi

if git ls-files --others --exclude-standard services/brain-api/src/aion_brain/api \
  | rg -v '^services/brain-api/src/aion_brain/api/connector_runtime\.py$|^services/brain-api/src/aion_brain/api/connector_simulator\.py$|^services/brain-api/src/aion_brain/api/connector_policy\.py$|^services/brain-api/src/aion_brain/api/connector_sandbox\.py$|^services/brain-api/src/aion_brain/api/connector_credentials\.py$' \
  | rg -n '.'; then
  echo "AION-106 must not add API router files" >&2
  exit 1
fi

if git diff --name-only --diff-filter=ACMRT HEAD -- packages/aion-sdk-python/src/aion_sdk/resources packages/aion-sdk-python/src/aion_sdk/cli.py packages/aion-sdk-python/src/aion_sdk/cli \
  | rg -v '^packages/aion-sdk-python/src/aion_sdk/resources/connector_runtime\.py$|^packages/aion-sdk-python/src/aion_sdk/resources/connector_simulator\.py$|^packages/aion-sdk-python/src/aion_sdk/resources/connector_policy\.py$|^packages/aion-sdk-python/src/aion_sdk/resources/connector_sandbox\.py$|^packages/aion-sdk-python/src/aion_sdk/resources/connector_credentials\.py$|^packages/aion-sdk-python/src/aion_sdk/cli/commands/connector_runtime\.py$|^packages/aion-sdk-python/src/aion_sdk/cli/commands/connector_simulator\.py$|^packages/aion-sdk-python/src/aion_sdk/cli/commands/connector_policy\.py$|^packages/aion-sdk-python/src/aion_sdk/cli/commands/connector_sandbox\.py$|^packages/aion-sdk-python/src/aion_sdk/cli/commands/connector_credentials\.py$|^packages/aion-sdk-python/src/aion_sdk/cli/main\.py$' \
  | rg -n '.'; then
  echo "AION-106 must not add SDK resources or CLI command implementations" >&2
  exit 1
fi

if git ls-files --others --exclude-standard packages/aion-sdk-python/src/aion_sdk/resources packages/aion-sdk-python/src/aion_sdk/cli.py packages/aion-sdk-python/src/aion_sdk/cli \
  | rg -v '^packages/aion-sdk-python/src/aion_sdk/resources/connector_runtime\.py$|^packages/aion-sdk-python/src/aion_sdk/resources/connector_simulator\.py$|^packages/aion-sdk-python/src/aion_sdk/resources/connector_policy\.py$|^packages/aion-sdk-python/src/aion_sdk/resources/connector_sandbox\.py$|^packages/aion-sdk-python/src/aion_sdk/resources/connector_credentials\.py$|^packages/aion-sdk-python/src/aion_sdk/cli/commands/connector_runtime\.py$|^packages/aion-sdk-python/src/aion_sdk/cli/commands/connector_simulator\.py$|^packages/aion-sdk-python/src/aion_sdk/cli/commands/connector_policy\.py$|^packages/aion-sdk-python/src/aion_sdk/cli/commands/connector_sandbox\.py$|^packages/aion-sdk-python/src/aion_sdk/cli/commands/connector_credentials\.py$|^packages/aion-sdk-python/src/aion_sdk/cli/main\.py$' \
  | rg -n '.'; then
  echo "AION-106 must not add untracked SDK resources or CLI command implementations" >&2
  exit 1
fi

if rg -n 'https?://' "${required_docs[@]}" "${required_examples[@]}"; then
  echo "external URL or endpoint found in AION-106 connector artifacts" >&2
  exit 1
fi

if rg -n 'npm[[:space:]]+install|pnpm[[:space:]]+install|yarn[[:space:]]+add|bun[[:space:]]+add|pip[[:space:]]+install' \
  "${required_docs[@]}" "${required_examples[@]}"; then
  echo "package install instruction found in AION-106 connector artifacts" >&2
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
    Path("docs/connectors/external-connector-boundary-design.md"),
    Path("docs/connectors/connector-trust-model.md"),
    Path("docs/connectors/connector-credential-boundary.md"),
    Path("docs/connectors/connector-egress-guard.md"),
    Path("docs/connectors/connector-ingress-guard.md"),
    Path("docs/connectors/connector-capability-declaration.md"),
    Path("docs/connectors/connector-threat-model.md"),
    Path("docs/connectors/connector-release-gates.md"),
    Path("docs/connectors/connector-no-go-regression-pack.md"),
    Path("docs/connectors/future-connector-implementation-prerequisites.md"),
    Path("docs/adr/0097-external-connector-boundary-design.md"),
]
required_examples = [
    Path("examples/connectors/connector-boundary-design.json"),
    Path("examples/connectors/connector-trust-model.json"),
    Path("examples/connectors/connector-threat-model.json"),
    Path("examples/connectors/connector-release-gates.json"),
    Path("examples/connectors/connector-no-go-regression-result.json"),
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

allowed_review_prefixes = (
    "docs/",
    "examples/",
    "services/brain-api/tests/",
)
allowed_review_files = {
    "scripts/connector-boundary-design-check.sh",
    "scripts/connector-no-go-regression.sh",
    "scripts/connector-runtime-check.sh",
}
allowed_aion108_prefixes = (
    "services/brain-api/src/aion_brain/connector_runtime/",
)
allowed_aion110_prefixes = (
    "services/brain-api/src/aion_brain/connector_simulator/",
)
allowed_aion111_prefixes = (
    "services/brain-api/src/aion_brain/connector_policy/",
)
allowed_aion112_prefixes = (
    "services/brain-api/src/aion_brain/connector_sandbox/",
)
allowed_aion113_prefixes = (
    "services/brain-api/src/aion_brain/connector_credentials/",
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
    "services/brain-api/src/aion_brain/api_support/app_factory.py",
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
allowed_aion111_files = {
    "operator-console-static/demo-data/connector-policy-catalog.json",
    "operator-console-static/demo-data/connector-policy-dry-run.json",
    "packages/aion-sdk-python/src/aion_sdk/cli/commands/connector_policy.py",
    "packages/aion-sdk-python/src/aion_sdk/resources/connector_policy.py",
    "packages/aion-sdk-python/tests/test_cli_connector_policy.py",
    "packages/aion-sdk-python/tests/test_connector_policy_resource.py",
    "services/brain-api/src/aion_brain/api/connector_policy.py",
    "services/brain-api/src/aion_brain/contracts/connector_policy.py",
}
allowed_aion112_files = {
    "operator-console-static/demo-data/connector-sandbox-status.json",
    "operator-console-static/demo-data/connector-sandbox-readiness.json",
    "packages/aion-sdk-python/src/aion_sdk/cli/commands/connector_sandbox.py",
    "packages/aion-sdk-python/src/aion_sdk/resources/connector_sandbox.py",
    "packages/aion-sdk-python/tests/test_cli_connector_sandbox.py",
    "packages/aion-sdk-python/tests/test_connector_sandbox_resource.py",
    "services/brain-api/src/aion_brain/api/connector_sandbox.py",
    "services/brain-api/src/aion_brain/contracts/connector_sandbox.py",
}
allowed_aion113_files = {
    "operator-console-static/demo-data/connector-credential-boundary.json",
    "operator-console-static/demo-data/connector-credential-readiness.json",
    "packages/aion-sdk-python/src/aion_sdk/cli/commands/connector_credentials.py",
    "packages/aion-sdk-python/src/aion_sdk/resources/connector_credentials.py",
    "packages/aion-sdk-python/tests/test_cli_connector_credentials.py",
    "packages/aion-sdk-python/tests/test_connector_credentials_resource.py",
    "services/brain-api/src/aion_brain/api/connector_credentials.py",
    "services/brain-api/src/aion_brain/contracts/connector_credentials.py",
}
allowed_aion120_files = {
    "operator-console-static/demo-data/v02-planning-stabilization.json",
    "operator-console-static/demo-data/v02-implementation-readiness-scorecard.json",
}
allowed_aion121_files = {
    "operator-console-static/demo-data/v02-readiness-final-review.json",
    "operator-console-static/demo-data/v02-implementation-approval-guard.json",
}
allowed_aion122_files = {
    "operator-console-static/demo-data/v02-implementation-kickoff-boundary.json",
    "operator-console-static/demo-data/v02-runtime-workstream-lock.json",
}
allowed_aion123_files = {
    "operator-console-static/demo-data/v02-approval-workflow-stabilization.json",
    "operator-console-static/demo-data/v02-implementation-request-intake.json",
}
allowed_aion124_files = {
    "operator-console-static/demo-data/v02-workstream-intake-readiness.json",
    "operator-console-static/demo-data/v02-implementation-sequencing-freeze.json",
}
allowed_aion125_files = {
    "operator-console-static/demo-data/v02-preimplementation-master-freeze.json",
    "operator-console-static/demo-data/v02-final-planning-baseline.json",
}
allowed_aion151_files = {
    "operator-console-static/demo-data/v02-production-auth-authorization.json",
    "operator-console-static/demo-data/v02-production-auth-runtime-guard-hold.json",
}
allowed_aion153_files = {
    "operator-console-static/demo-data/v02-production-auth-core-implementation-closeout.json",
    "operator-console-static/demo-data/v02-production-auth-stabilization-authorization.json",
}
allowed_aion154_files = {
    "operator-console-static/demo-data/production-auth-core-stabilization.json",
    "operator-console-static/demo-data/production-auth-core-stabilization-runtime-hold.json",
}
allowed_aion155_files = {
    "operator-console-static/demo-data/v02-production-auth-request-boundary-authorization.json",
}
allowed_aion156_files = {
    "operator-console-static/demo-data/production-auth-request-identity-boundary.json",
    "operator-console-static/demo-data/production-auth-request-identity-runtime-hold.json",
    "services/brain-api/src/aion_brain/contracts/request_identity.py",
    "services/brain-api/src/aion_brain/config.py",
    "services/brain-api/src/aion_brain/kernel/app_factory.py",
    "services/brain-api/src/aion_brain/kernel/container.py",
    "services/brain-api/src/aion_brain/kernel/diagnostics.py",
}
allowed_aion157_files = {
    "operator-console-static/demo-data/v02-production-auth-request-identity-stabilization-authorization.json",
}
allowed_aion152_prefixes = (
    "services/brain-api/src/aion_brain/production_auth/",
)
allowed_aion152_files = {
    "services/brain-api/src/aion_brain/local_auth/audit.py",
    "services/brain-api/src/aion_brain/contracts/production_auth.py",
}
runtime_prefixes = (
    "services/brain-api/src/",
    "packages/aion-sdk-python/src/",
    "operator-console-static/",
)

runtime_patterns = {
    "connector runtime": re.compile(r"\bConnector(Runtime|Client|Adapter|Transport)\b|\bconnector[_\-\s]*runtime\b", re.I),
    "network client": re.compile(r"\b(requests\.(get|post|put|patch|delete)|httpx\.(get|post|put|patch|delete)|aiohttp\.ClientSession|urllib\.request)\b", re.I),
    "connector sdk dependency": re.compile(r"\b(connector[_\-\s]*sdk|provider[_\-\s]*sdk|external[_\-\s]*sdk)\b", re.I),
    "credential storage": re.compile(r"\b(credential|secret|password)[_\-\s]*(store|storage|vault|value)\b", re.I),
    "token storage": re.compile(r"\b(access[_\-\s]*token|refresh[_\-\s]*token|id[_\-\s]*token|token[_\-\s]*(store|storage|issuer))\b", re.I),
    "dynamic route registration": re.compile(r"\b(add_api_route|include_router|dynamic[_\-\s]*(api[_\-\s]*)?route)\b", re.I),
    "connector activation enabled": re.compile(r"\b(connector_runtime_enabled|connector_activation_enabled|activation_enabled)\s*[:=]\s*true\b", re.I),
    "external calls enabled": re.compile(r"\b(external_calls_enabled|network_calls_enabled|egress_enabled)\s*[:=]\s*true\b", re.I),
    "raw prompt egress": re.compile(r"\braw_prompt[_\-\s]*egress[_\-\s]*allowed\s*[:=]\s*true\b", re.I),
    "hidden reasoning egress": re.compile(r"\bhidden_reasoning[_\-\s]*egress[_\-\s]*allowed\s*[:=]\s*true\b", re.I),
    "secret egress": re.compile(r"\bsecret[_\-\s]*egress[_\-\s]*allowed\s*[:=]\s*true\b", re.I),
    "policy bypass": re.compile(r"\bpolicy_bypass(_enabled)?\s*[:=]\s*true\b", re.I),
    "audit bypass": re.compile(r"\baudit_bypass(_enabled)?\s*[:=]\s*true\b", re.I),
}

for relative in sorted(changed):
    path = root / relative
    if not path.is_file():
        continue
    if (
        relative in allowed_review_files
        or relative in allowed_aion108_files
        or relative in allowed_aion110_files
        or relative in allowed_aion111_files
        or relative in allowed_aion112_files
        or relative in allowed_aion113_files
        or relative in allowed_aion120_files
        or relative in allowed_aion121_files
        or relative in allowed_aion122_files
        or relative in allowed_aion123_files
        or relative in allowed_aion124_files
        or relative in allowed_aion125_files
        or relative in allowed_aion151_files
        or relative in allowed_aion153_files
        or relative in allowed_aion154_files
        or relative in allowed_aion155_files
        or relative in allowed_aion156_files
        or relative in allowed_aion157_files
        or relative in allowed_aion152_files
        or relative.startswith(allowed_review_prefixes)
        or relative.startswith(allowed_aion108_prefixes)
        or relative.startswith(allowed_aion110_prefixes)
        or relative.startswith(allowed_aion111_prefixes)
        or relative.startswith(allowed_aion112_prefixes)
        or relative.startswith(allowed_aion113_prefixes)
        or relative.startswith(allowed_aion152_prefixes)
    ):
        continue
    if not relative.startswith(runtime_prefixes):
        continue
    text = path.read_text(errors="ignore")
    for label, pattern in runtime_patterns.items():
        if pattern.search(text):
            raise SystemExit(f"connector runtime pattern found in {relative}: {label}")

for doc in required_docs:
    text = (root / doc).read_text().lower()
    if not any(marker in text for marker in ("disabled", "no-go", "absent", "untrusted", "runtime")):
        raise SystemExit(f"AION-106 doc must state disabled/no-go/absent/untrusted posture: {doc}")

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
        raise SystemExit(f"blocked marker found in AION-106 examples: {marker}")

false_keys = {
    "connector_runtime_enabled",
    "external_calls_enabled",
    "credentials_present",
    "token_storage_enabled",
    "dynamic_routes_enabled",
    "activation_enabled",
    "connector_sdk_dependency_present",
    "provider_sdk_dependency_present",
    "network_client_present",
    "policy_bypass_enabled",
    "audit_bypass_enabled",
    "contains_real_endpoints",
    "contains_secrets",
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

trust = examples["connector-trust-model.json"]
for key in (
    "untrusted_by_default",
    "metadata_untrusted",
    "returned_data_untrusted",
    "capability_claims_require_validation",
    "provenance_required",
    "policy_required",
    "audit_required",
    "redaction_required",
):
    if trust.get(key) is not True:
        raise SystemExit(f"connector trust model must set {key}=true")

threats = examples["connector-threat-model.json"].get("threats", [])
required_threats = {
    "credential exfiltration",
    "prompt injection through connector response",
    "malicious connector metadata",
    "overbroad scopes",
    "SSRF-style egress abuse",
    "data exfiltration",
    "stale response trust",
    "rate limit exhaustion",
    "audit tampering",
    "policy bypass",
    "action authorization bypass",
    "hidden external calls",
    "provider impersonation",
    "dependency confusion",
}
threat_names = {item.get("threat") for item in threats}
missing = required_threats - threat_names
if missing:
    raise SystemExit(f"connector threat model missing threats: {sorted(missing)}")
for item in threats:
    for key in ("threat", "entry_point", "current_control", "future_required_control", "no_go_condition"):
        if not item.get(key):
            raise SystemExit(f"connector threat row missing {key}: {item}")

no_go = examples["connector-no-go-regression-result.json"]
for item in no_go.get("checks", []):
    if item.get("expected_status") != "passed" or item.get("present") is not False:
        raise SystemExit(f"connector no-go row must be passed and absent: {item}")

print("AION-106 connector no-go JSON and changed-file checks PASS")
PY

echo "Connector no-go regression result:"
echo "- connector_runtime: absent"
echo "- external_calls: absent"
echo "- credentials_tokens: absent"
echo "- connector_sdk_dependencies: absent"
echo "- dynamic_routes: absent"
echo "- policy_audit_bypass: absent"
echo "Connector no-go regression PASS"
