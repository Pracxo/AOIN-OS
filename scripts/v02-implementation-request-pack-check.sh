#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/portable-search.sh"

git_ref_exists() {
  git rev-parse --verify --quiet "$1" >/dev/null 2>&1
}

comparison_base() {
  local candidate
  local candidates=()
  if [[ -n "${GITHUB_BASE_REF:-}" ]]; then
    candidates+=("origin/${GITHUB_BASE_REF}" "${GITHUB_BASE_REF}")
  fi
  candidates+=(origin/main main)

  for candidate in "${candidates[@]}"; do
    if git_ref_exists "$candidate"; then
      git merge-base HEAD "$candidate" 2>/dev/null && return 0
    fi
  done
  if git_ref_exists HEAD~1; then
    printf '%s\n' "HEAD~1"
    return 0
  fi
  return 1
}

changed_files() {
  local base
  if base="$(comparison_base)"; then
    git diff --name-only --diff-filter=ACMRT "$base" HEAD --
  fi
  git diff --name-only --diff-filter=ACMRT --
  git diff --cached --name-only --diff-filter=ACMRT --
  git ls-files --others --exclude-standard
}

is_nested_gate_context() {
  [[ -n "${PYTEST_CURRENT_TEST:-}" ]] && return 0
  [[ "${AION_V02_IMPLEMENTATION_REQUEST_PACK_SKIP_INHERITED_GATES:-}" == "1" ]] && return 0
  [[ "${AION_AGGREGATE_GATE_RUNNING:-}" == "1" ]] && return 0
  [[ "${AION_CHECK_RUNNING:-}" == "1" ]] && return 0
  return 1
}

run_inherited_gate() {
  AION_AGGREGATE_GATE_RUNNING=1 AION_CHECK_RUNNING=1 "$@"
}

required_docs=(
  docs/release/v02-implementation-request-pack.md
  docs/release/v02-proposal-submission-templates.md
  docs/release/v02-approval-evidence-boundary.md
  docs/release/v02-implementation-request-evidence-checklist.md
  docs/release/v02-workstream-request-template-catalog.md
  docs/release/v02-request-package-review-rules.md
  docs/release/v02-request-package-no-go.md
  docs/adr/0122-v02-implementation-request-pack.md
)

required_examples=(
  examples/release/v02-implementation-request-pack.json
  examples/release/v02-proposal-submission-template.json
  examples/release/v02-approval-evidence-boundary.json
  examples/release/v02-implementation-request-evidence-checklist.json
  examples/release/v02-workstream-request-template-catalog.json
  operator-console-static/demo-data/v02-implementation-request-pack.json
  operator-console-static/demo-data/v02-proposal-submission-templates.json
)

for file in "${required_docs[@]}" "${required_examples[@]}"; do
  test -f "$file" || {
    echo "missing AION-131 request pack artifact: $file" >&2
    exit 1
  }
done

grep -q "0122-v02-implementation-request-pack.md" docs/adr/README.md || {
  echo "ADR 0122 is not indexed" >&2
  exit 1
}

if is_nested_gate_context; then
  echo "PASS: v0.2 request pack inherited gates deferred to outer aggregate gate"
else
  run_inherited_gate ./scripts/v02-planning-track-closeout.sh
  run_inherited_gate ./scripts/v02-planning-track-handoff-freeze.sh
  ./scripts/v02-planning-track-closeout-no-go-regression.sh
  run_inherited_gate ./scripts/v02-final-planning-release-gate.sh
  run_inherited_gate ./scripts/v02-planning-master-checkpoint.sh
  run_inherited_gate ./scripts/v02-proposal-registry-stabilization-gate.sh
  run_inherited_gate ./scripts/v02-workstream-proposal-registry-check.sh
  run_inherited_gate ./scripts/v02-preimplementation-master-freeze.sh
  ./scripts/docs-check.sh
  ./scripts/final-docs-audit.sh
  ./scripts/verify-no-domain-drift.sh
  ./scripts/boundary-check.sh
fi

./scripts/v02-request-pack-no-go-regression.sh

if git tag --list | rg -n '^(v0\.2|v0\.2\.0|aion-v0\.2\.0|aion-v0\.2)$'; then
  echo "v0.2 tag must not exist for AION-131" >&2
  exit 1
fi

for file in package.json package-lock.json pnpm-lock.yaml yarn.lock bun.lockb; do
  if find . -path './.git' -prune -o -type f -name "$file" -print | rg -n '.'; then
    echo "package manager file is not allowed for AION-131: $file" >&2
    exit 1
  fi
done

if changed_files | rg -n '^infra/postgres/migrations/|^services/brain-api/migrations/'; then
  echo "AION-131 must not add or change migrations" >&2
  exit 1
fi

if changed_files | rg -n '^services/brain-api/src/aion_brain/api/'; then
  echo "AION-131 must not add or change API runtime execution routes" >&2
  exit 1
fi

if changed_files | rg -n '^packages/aion-sdk-python/src/aion_sdk/(resources/|cli/commands/|client\.py|cli/main\.py)'; then
  echo "AION-131 must not add or change SDK resources or CLI implementations" >&2
  exit 1
fi

python3 - "$ROOT_DIR" <<'PY'
import json
import sys
from pathlib import Path

root = Path(sys.argv[1])
paths = [
    root / "examples/release/v02-implementation-request-pack.json",
    root / "examples/release/v02-proposal-submission-template.json",
    root / "examples/release/v02-approval-evidence-boundary.json",
    root / "examples/release/v02-implementation-request-evidence-checklist.json",
    root / "examples/release/v02-workstream-request-template-catalog.json",
    root / "operator-console-static/demo-data/v02-implementation-request-pack.json",
    root / "operator-console-static/demo-data/v02-proposal-submission-templates.json",
]
false_keys = {
    "request_package_implementation_approved",
    "proposal_template_implementation_approved",
    "approval_evidence_approval_true",
    "evidence_approves_implementation",
    "adr_review_enables_runtime",
    "gate_success_enables_runtime",
    "v02_tag_created",
    "v02_release_created",
    "v02_release_approved",
    "runtime_implementation_approved",
    "backlog_implementation_items_approved",
    "workstream_implementation_approved",
    "proposal_implementation_approved",
    "approval_queue_item_approved",
    "approval_workflow_bypassed",
    "approval_record_missing",
    "adr_dependency_bypassed",
    "gate_dependency_bypassed",
    "approval_expiry_bypassed",
    "approval_revocation_bypassed",
    "dual_control_bypassed",
    "operator_write_execution_approved",
    "connector_implementation_approved",
    "production_auth_approved",
    "module_activation_approved",
    "external_calls_approved",
    "credential_storage_approved",
    "token_storage_approved",
    "sandbox_execution_approved",
    "package_files_added",
    "migrations_added",
    "api_runtime_execution_route_added",
    "sdk_resource_implementation_added",
    "cli_command_implementation_added",
    "frontend_dependencies_added",
    "secrets_present",
    "tokens_present",
    "credentials_present",
    "credential_values_present",
    "token_values_present",
    "endpoints_present",
    "prompt_payloads_present",
    "private_reasoning_present",
}


def assert_false_keys(value, context):
    if isinstance(value, dict):
        for key, nested in value.items():
            if key in false_keys and nested is not False:
                raise SystemExit(f"{context}.{key} must be false")
            if key in {"implementation_approved", "approval_state", "default_approval_status", "implementation_allowed_today"} and nested is not False:
                raise SystemExit(f"{context}.{key} must be false")
            assert_false_keys(nested, f"{context}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            assert_false_keys(item, f"{context}[{index}]")


for path in paths:
    payload = json.loads(path.read_text())
    if payload.get("task_id") != "AION-131":
        raise SystemExit(f"{path} must identify AION-131")
    if payload.get("status") != "passed":
        raise SystemExit(f"{path} must be passed")
    if payload.get("synthetic") is not True:
        raise SystemExit(f"{path} must be synthetic")
    if payload.get("v02_implementation_request_pack_created") is not True:
        raise SystemExit(f"{path} must mark request pack created")
    if payload.get("proposal_templates_created") is not True:
        raise SystemExit(f"{path} must mark proposal templates created")
    if payload.get("approval_evidence_boundary_created") is not True:
        raise SystemExit(f"{path} must mark approval evidence boundary created")
    if payload.get("request_pack_preview_only") is not True:
        raise SystemExit(f"{path} must keep request pack preview-only")
    if payload.get("proposal_registry_preview_only") is not True:
        raise SystemExit(f"{path} must keep proposal registry preview-only")
    if payload.get("approval_queue_preview_only") is not True:
        raise SystemExit(f"{path} must keep approval queue preview-only")
    assert_false_keys(payload, str(path))

for path in paths[-2:]:
    payload = json.loads(path.read_text())
    if payload.get("read_only") is not True:
        raise SystemExit(f"{path} must be read-only static data")
    if payload.get("redaction_applied") is not True:
        raise SystemExit(f"{path} must mark redaction applied")

print("AION-131 JSON examples valid")
PY

cat <<'SUMMARY'
v0.2 implementation request pack check result:
- v02_implementation_request_pack_created: true
- proposal_templates_created: true
- approval_evidence_boundary_created: true
- request_pack_preview_only: true
- proposal_registry_preview_only: true
- approval_queue_preview_only: true
- approval_queue_item_approved: false
- proposal_implementation_approved: false
- runtime_implementation_approved: false
- workstream_implementation_approved: false
- v02_tag_created: false
- v02_release_created: false
v0.2 implementation request pack check PASS
SUMMARY
