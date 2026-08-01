#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/python-selection.sh"
source "$ROOT_DIR/scripts/lib/immutable-tags.sh"
source "$ROOT_DIR/scripts/lib/portable-search.sh"

PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"
export AION_BRAIN_PYTHON="$PYTHON_BIN"

git_ref_exists() {
  git rev-parse --verify --quiet "$1" >/dev/null 2>&1
}

comparison_base() {
  local candidate
  local merge_base
  if [[ -n "${GITHUB_BASE_REF:-}" ]]; then
    for candidate in "origin/${GITHUB_BASE_REF}" "${GITHUB_BASE_REF}"; do
      if git_ref_exists "$candidate"; then
        merge_base="$(git merge-base HEAD "$candidate" 2>/dev/null || true)"
        if [[ -n "$merge_base" ]]; then
          echo "$merge_base"
          return 0
        fi
      fi
    done
  fi
  for candidate in origin/main main; do
    if git_ref_exists "$candidate"; then
      merge_base="$(git merge-base HEAD "$candidate" 2>/dev/null || true)"
      if [[ -n "$merge_base" ]]; then
        echo "$merge_base"
        return 0
      fi
    fi
  done
  if git_ref_exists HEAD~1; then
    echo "HEAD~1"
    return 0
  fi
  return 1
}

changed_paths() {
  local base
  base="$(comparison_base || true)"
  if [[ -n "$base" ]]; then
    git diff --name-only --diff-filter=ACMRT "$base" HEAD --
  fi
  git diff --name-only --diff-filter=ACMRT HEAD --
  git diff --cached --name-only --diff-filter=ACMRT --
  git ls-files --others --exclude-standard --
}

is_allowed_path() {
  case "$1" in
    README.md|AGENTS.md|\
    docs/adr/README.md|\
    docs/adr/0202-final-secure-runtime-integration-evaluation-and-v02-release-qualification-program-authorization.md|\
    docs/adr/0203-disabled-v02-production-readiness-qualification-foundation.md|\
    docs/architecture.md|docs/brain-contract.md|docs/policy-model.md|docs/project-status.md|docs/visual-brain.md|\
    docs/v02-release-qualification/*|\
    docs/release/v02-release-qualification-*|\
    docs/release/v02-qualification-foundation-operator-evaluation-*|\
    docs/release/v02-staging-qualification-*|\
    docs/release/v02-release-readiness-delta.md|\
    examples/v02-release-qualification/*|\
    operator-console-static/index.html|operator-console-static/app.js|operator-console-static/README.md|\
    operator-console-static/demo-data/v02-release-qualification-*.json|\
    operator-console-static/demo-data/v02-qualification-foundation-operator-evaluation.json|\
    operator-console-static/demo-data/v02-staging-qualification-authorization.json|\
    operator-console-static/demo-data/v02-staging-environment-profile.json|\
    operator-console-static/demo-data/v02-staging-build-plan.json|\
    operator-console-static/demo-data/v02-staging-artifact-boundary.json|\
    operator-console-static/demo-data/v02-staging-rollback-boundary.json|\
    operator-console-static/demo-data/v02-staging-runtime-hold.json|\
    scripts/auth-design-check.sh|\
    scripts/capability-runtime-authorization-check.sh|\
    scripts/capability-runtime-authorization-no-go-regression.sh|\
    scripts/capability-runtime-check.sh|\
    scripts/capability-runtime-no-go-regression.sh|\
    scripts/capability-runtime-operator-evaluation-no-go-regression.sh|\
    scripts/connector-no-go-regression.sh|\
    scripts/connector-runtime-no-external-call-regression.sh|\
    scripts/knowledge-intelligence-claim-graph-operator-evaluation-no-go-regression.sh|\
    scripts/knowledge-intelligence-domain-expert-mesh-authorization-no-go-regression.sh|\
    scripts/knowledge-intelligence-domain-expert-mesh-no-go-regression.sh|\
    scripts/knowledge-intelligence-domain-expert-mesh-operator-evaluation-no-go-regression.sh|\
    scripts/knowledge-intelligence-epistemic-assessment-operator-evaluation-no-go-regression.sh|\
    scripts/knowledge-intelligence-integrated-research-agent-operator-evaluation-no-go-regression.sh|\
    scripts/knowledge-intelligence-program-final-evaluation-no-go-regression.sh|\
    scripts/knowledge-intelligence-research-operator-evaluation-no-go-regression.sh|\
    scripts/knowledge-intelligence-tool-verification-authorization-no-go-regression.sh|\
    scripts/knowledge-intelligence-verified-knowledge-authorization-no-go-regression.sh|\
    scripts/knowledge-intelligence-verified-memory-operator-evaluation-no-go-regression.sh|\
    scripts/lib/cognitive_architecture_governance.py|\
    scripts/lib/v02-production-auth-scan-exclusions.sh|\
    scripts/model-gateway-authorization-check.sh|\
    scripts/model-gateway-authorization-no-go-regression.sh|\
    scripts/model-gateway-check.sh|\
    scripts/model-gateway-no-go-regression.sh|\
    scripts/model-gateway-operator-evaluation-no-go-regression.sh|\
    scripts/operator-console-integration-authorization-no-go-regression.sh|\
    scripts/secure-runtime-foundation-operator-evaluation-no-go-regression.sh|\
    scripts/secure-runtime-integration-program-no-go-regression.sh|\
    scripts/static-console-safety-check.sh|\
    scripts/lib/v02_release_qualification_foundation_operator_evaluation.py|\
    scripts/secure-runtime-foundation-check.sh|\
    scripts/secure-runtime-foundation-no-go-regression.sh|\
    scripts/v02-release-qualification-program-authorization-check.sh|\
    scripts/v02-release-qualification-program-authorization-no-go-regression.sh|\
    scripts/v02-release-qualification-runtime-hold.sh|\
    scripts/v02-release-qualification-foundation-check.sh|\
    scripts/v02-release-qualification-foundation-no-go-regression.sh|\
    scripts/v02-release-qualification-foundation-operator-evaluation-check.sh|\
    scripts/v02-release-qualification-foundation-operator-evaluation-no-go-regression.sh|\
    scripts/v02-release-qualification-foundation-pilot-evidence-check.sh|\
    scripts/v02-release-qualification-foundation-runtime-hold.sh|\
    scripts/v02-release-qualification-local-run.py|\
    scripts/v02-staging-qualification-authorization-check.sh|\
    scripts/v02-staging-qualification-authorization-no-go-regression.sh|\
    scripts/v02-staging-qualification-runtime-hold.sh|\
    scripts/secure-runtime-integration-final-evaluation-no-go-regression.sh|\
    services/brain-api/src/aion_brain/contracts/v02_release_qualification.py|\
    services/brain-api/src/aion_brain/v02_release_qualification/*.py|\
    services/brain-api/tests/test_secure_runtime_integration_final_closeout_aion238.py|\
    services/brain-api/tests/test_governed_learning_memory_no_runtime_source.py|\
    services/brain-api/tests/test_knowledge_epistemic_assessment_evaluation_repository_integrity.py|\
    services/brain-api/tests/test_knowledge_intelligence_program_repository_integrity.py|\
    services/brain-api/tests/test_knowledge_research_evaluation_repository_integrity.py|\
    services/brain-api/tests/test_knowledge_source_registry_evaluation_no_side_effects.py|\
    services/brain-api/tests/test_self_improvement_shadow_activation_evaluation_repository_integrity.py|\
    services/brain-api/tests/test_self_improvement_shadow_activation_scope_spec.py|\
    services/brain-api/tests/test_v02_release_qualification_*.py)
      return 0
      ;;
  esac
  return 1
}

while IFS= read -r path; do
  [[ -z "$path" ]] && continue
  if ! is_allowed_path "$path"; then
    echo "AION-239 changed path outside release-qualification boundary: $path" >&2
    exit 1
  fi
done < <(changed_paths | sort -u)

if changed_paths | sort -u | rg -n '^\.github/workflows/' >/dev/null 2>&1; then
  echo "AION-239 must not modify GitHub workflows" >&2
  exit 1
fi
if changed_paths | sort -u | rg -n '(^|/)(package(-lock)?\.json|pnpm-lock\.yaml|yarn\.lock|pyproject\.toml)$' >/dev/null 2>&1; then
  echo "AION-239 must not modify package manifests or lockfiles" >&2
  exit 1
fi
if changed_paths | sort -u | rg -n '(^migrations/|/migrations/)' >/dev/null 2>&1; then
  echo "AION-239 must not add migrations" >&2
  exit 1
fi

while IFS= read -r path; do
  [[ -z "$path" ]] && continue
  case "$path" in
    services/brain-api/src/aion_brain/contracts/v02_release_qualification.py|\
    services/brain-api/src/aion_brain/v02_release_qualification/*.py)
      ;;
    services/brain-api/src/aion_brain/*)
      echo "AION-239 must not modify completed runtime source: $path" >&2
      exit 1
      ;;
  esac
done < <(changed_paths | sort -u)

PYTHONPATH="$ROOT_DIR/services/brain-api/src:${PYTHONPATH:-}" "$PYTHON_BIN" - <<'PY'
from __future__ import annotations

import ast
import json
from pathlib import Path

from aion_brain.contracts import v02_release_qualification as c

root = Path.cwd()
runtime_root = root / "services/brain-api/src/aion_brain/v02_release_qualification"
contract = root / "services/brain-api/src/aion_brain/contracts/v02_release_qualification.py"
expected = {
    "__init__.py",
    "authorization.py",
    "gap_matrix.py",
    "production_auth_composition.py",
    "request_identity.py",
    "replay_provisioning.py",
    "identity_provider.py",
    "key_lifecycle.py",
    "protected_material.py",
    "credential_lifecycle.py",
    "token_lifecycle.py",
    "session_lifecycle.py",
    "deployment_manifest.py",
    "artifact_provenance.py",
    "rollback.py",
    "observability.py",
    "threat_model.py",
    "runtime_guard.py",
    "release_gate.py",
    "integrity.py",
    "evidence.py",
}
if {path.name for path in runtime_root.glob("*.py")} != expected:
    raise SystemExit("AION-239 runtime source scope mismatch")
blocked = (
    "network.py",
    "live_identity_provider.py",
    "secret_store.py",
    "credential_store.py",
    "token_store.py",
    "live_replay_ledger.py",
    "database.py",
    "deployer.py",
    "kubernetes.py",
    "terraform.py",
    "container_registry.py",
    "production_observability_exporter.py",
    "release_publisher.py",
    "background_worker.py",
    "scheduler.py",
)
for name in blocked:
    if (runtime_root / name).exists():
        raise SystemExit(f"blocked runtime source exists: {name}")
if (root / "services/brain-api/src/aion_brain/api/v02_release_qualification.py").exists():
    raise SystemExit("AION-239 must not add an API route")

prohibited_imports = {
    "aiohttp",
    "boto3",
    "docker",
    "google.cloud",
    "httpx",
    "kubernetes",
    "os.environ",
    "requests",
    "socket",
    "ssl",
    "subprocess",
    "terraform",
    "urllib" ".request",
}
prohibited_calls = {"open", "exec", "eval"}
prohibited_attrs = {"write", "write_text", "write_bytes", "mkdir", "rename", "unlink"}
for path in [contract, *sorted(runtime_root.glob("*.py"))]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name in prohibited_imports:
                    raise SystemExit(f"prohibited import in {path}: {alias.name}")
        if isinstance(node, ast.ImportFrom) and (node.module or "") in prohibited_imports:
            raise SystemExit(f"prohibited import in {path}: {node.module}")
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name) and func.id in prohibited_calls:
                raise SystemExit(f"prohibited call in {path}: {func.id}")
            if isinstance(func, ast.Attribute) and func.attr in prohibited_attrs:
                raise SystemExit(f"prohibited filesystem call in {path}: {func.attr}")
        if isinstance(node, ast.Attribute):
            full = f"{node.value.id}.{node.attr}" if isinstance(node.value, ast.Name) else node.attr
            if full in prohibited_imports:
                raise SystemExit(f"prohibited attribute in {path}: {full}")

for ledger in (
    Path("docs/v02-release-qualification/program-ledger.json"),
    Path("docs/v02-release-qualification/authorization-ledger.json"),
):
    payload = json.loads(ledger.read_text(encoding="utf-8"))
    for key, expected_false in payload.get("prohibited_capabilities", {}).items():
        if expected_false is not False:
            raise SystemExit(f"{ledger} must keep {key}=false")
    for key in payload.get("zero_resource_limit_keys", []):
        if payload["resource_limits"][key] != 0:
            raise SystemExit(f"{ledger} must keep {key}=0")
    if payload.get("v02_release_ready") is not False:
        raise SystemExit(f"{ledger} must keep v02_release_ready=false")
    if payload.get("v02_tag_created") is not False:
        raise SystemExit(f"{ledger} must keep v02_tag_created=false")
    if payload.get("v02_release_created") is not False:
        raise SystemExit(f"{ledger} must keep v02_release_created=false")

evidence = json.loads(
    Path(
        "examples/v02-release-qualification/"
        "v02-production-readiness-qualification-foundation-pilot-evidence.json"
    ).read_text(encoding="utf-8")
)
if evidence["prohibited_effect_counters"] != c.PROHIBITED_EFFECT_COUNTERS:
    raise SystemExit("pilot evidence prohibited counters mismatch")
if any(evidence[key] != 0 for key in c.PROHIBITED_EFFECT_COUNTERS):
    raise SystemExit("pilot evidence top-level prohibited counter is non-zero")
PY

aion_confirm_immutable_v01_tag_history >/dev/null
if git tag --list 'v0.2*' 'aion-v0.2*' | rg -n '.+' >/dev/null 2>&1; then
  echo "AION-239 must not create a v0.2 tag" >&2
  exit 1
fi

echo "v0.2 release qualification foundation no-go PASS"
