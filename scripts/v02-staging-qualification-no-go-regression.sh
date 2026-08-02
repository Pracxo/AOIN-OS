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
    docs/adr/README.md|docs/adr/0205-controlled-isolated-local-staging-artifact-build-and-rollback-drill.md|\
    docs/architecture.md|docs/brain-contract.md|docs/policy-model.md|docs/project-status.md|docs/visual-brain.md|\
    docs/v02-release-qualification/*|\
    docs/release/v02-staging-qualification-*|\
    examples/v02-release-qualification/*|\
    operator-console-static/README.md|operator-console-static/app.js|operator-console-static/index.html|\
    operator-console-static/demo-data/v02-release-qualification-staging-*.json|\
    scripts/v02-staging-qualification-authorization-check.sh|\
    scripts/v02-staging-qualification-authorization-no-go-regression.sh|\
    scripts/v02-staging-qualification-check.sh|\
    scripts/v02-staging-qualification-local-run.py|\
    scripts/v02-staging-qualification-no-go-regression.sh|\
    scripts/v02-staging-qualification-pilot-evidence-check.sh|\
    scripts/v02-staging-qualification-runtime-hold.sh|\
    scripts/v02-release-qualification-foundation-check.sh|\
    scripts/v02-release-qualification-foundation-no-go-regression.sh|\
    scripts/v02-release-qualification-foundation-operator-evaluation-no-go-regression.sh|\
    scripts/v02-release-qualification-foundation-runtime-hold.sh|\
    scripts/v02-release-qualification-program-authorization-check.sh|\
    scripts/v02-release-qualification-program-authorization-no-go-regression.sh|\
    services/brain-api/src/aion_brain/contracts/v02_staging_qualification.py|\
    services/brain-api/src/aion_brain/v02_staging_qualification/*.py|\
    services/brain-api/tests/test_v02_staging_qualification_aion241.py)
      return 0
      ;;
  esac
  return 1
}

while IFS= read -r path; do
  [[ -z "$path" ]] && continue
  if ! is_allowed_path "$path"; then
    echo "AION-241 changed path outside controlled staging qualification boundary: $path" >&2
    exit 1
  fi
done < <(changed_paths | sort -u)

if changed_paths | sort -u | rg -n '^\.github/workflows/' >/dev/null 2>&1; then
  echo "AION-241 must not modify GitHub workflows" >&2
  exit 1
fi
if changed_paths | sort -u | rg -n '(^|/)(package(-lock)?\.json|pnpm-lock\.yaml|yarn\.lock|bun\.lockb|pyproject\.toml)$' >/dev/null 2>&1; then
  echo "AION-241 must not modify dependency manifests or lockfiles" >&2
  exit 1
fi
if changed_paths | sort -u | rg -n '(^migrations/|/migrations/)' >/dev/null 2>&1; then
  echo "AION-241 must not add migrations" >&2
  exit 1
fi
if changed_paths | sort -u | rg -n '(^|/)Dockerfile$|^docker-compose\.yml$|^docker-compose\.yaml$' >/dev/null 2>&1; then
  echo "AION-241 must not modify canonical Docker files" >&2
  exit 1
fi
if changed_paths | sort -u | rg -n '^aion-v0\.1\.0($|/)' >/dev/null 2>&1; then
  echo "AION-241 must not move or modify aion-v0.1.0" >&2
  exit 1
fi
while IFS= read -r path; do
  [[ -z "$path" ]] && continue
  case "$path" in
    services/brain-api/src/aion_brain/contracts/v02_staging_qualification.py|\
    services/brain-api/src/aion_brain/v02_staging_qualification/*.py)
      ;;
    services/brain-api/src/aion_brain/v02_release_qualification/*|\
    services/brain-api/src/aion_brain/secure_runtime_integration/*)
      echo "AION-241 must not modify completed release-qualification or SRI runtime source: $path" >&2
      exit 1
      ;;
  esac
done < <(changed_paths | sort -u)

PYTHONPATH="$ROOT_DIR/services/brain-api/src:${PYTHONPATH:-}" "$PYTHON_BIN" - <<'PY'
from __future__ import annotations

import ast
import importlib.util
import json
import sys
from pathlib import Path

from aion_brain.contracts import v02_staging_qualification as c

root = Path.cwd()
runtime_root = root / "services/brain-api/src/aion_brain/v02_staging_qualification"
contract = root / "services/brain-api/src/aion_brain/contracts/v02_staging_qualification.py"
runner_path = root / "scripts/v02-staging-qualification-local-run.py"
expected_runtime = {
    "__init__.py",
    "authorization.py",
    "component_binding.py",
    "source_snapshot.py",
    "build_plan.py",
    "artifact_manifest.py",
    "sbom.py",
    "provenance.py",
    "environment_profile.py",
    "identity_fixture.py",
    "replay_fixture.py",
    "deployment_plan.py",
    "health_readiness.py",
    "observability.py",
    "security_validation.py",
    "rollback.py",
    "cleanup.py",
    "integrity.py",
    "evidence.py",
}
if {path.name for path in runtime_root.glob("*.py")} != expected_runtime:
    raise SystemExit("AION-241 runtime source scope mismatch")
for relative in c.REQUIRED_SOURCE_SCOPE:
    if not (root / relative).is_file():
        raise SystemExit(f"missing AION-241 source: {relative}")
for relative in c.PROHIBITED_SOURCE_SCOPE:
    if (root / relative).exists():
        raise SystemExit(f"prohibited AION-241 source exists: {relative}")

prohibited_imports = {
    "aiohttp",
    "boto3",
    "docker",
    "google.cloud",
    "httpx",
    "kubernetes",
    "os",
    "pathlib",
    "psycopg",
    "redis",
    "requests",
    "socket",
    "sqlalchemy",
    "ssl",
    "subprocess",
    "terraform",
    "urllib.request",
}
prohibited_calls = {"open", "exec", "eval", "__import__"}
prohibited_attrs = {
    "connect",
    "create_connection",
    "getenv",
    "mkdir",
    "rename",
    "resolve",
    "run",
    "unlink",
    "write",
    "write_bytes",
    "write_text",
}
for path in [contract, *sorted(runtime_root.glob("*.py"))]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name in prohibited_imports:
                    raise SystemExit(f"prohibited runtime import in {path}: {alias.name}")
        if isinstance(node, ast.ImportFrom) and (node.module or "") in prohibited_imports:
            raise SystemExit(f"prohibited runtime import in {path}: {node.module}")
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name) and func.id in prohibited_calls:
                raise SystemExit(f"prohibited runtime call in {path}: {func.id}")
            if isinstance(func, ast.Attribute) and func.attr in prohibited_attrs:
                raise SystemExit(f"prohibited runtime side-effect call in {path}: {func.attr}")
        if isinstance(node, ast.Attribute):
            if isinstance(node.value, ast.Name) and f"{node.value.id}.{node.attr}" == "os.environ":
                raise SystemExit(f"prohibited environment access in {path}: os.environ")

runner_text = runner_path.read_text(encoding="utf-8")
required_runner_markers = (
    "shell=False",
    "assert_allowed_docker_command",
    "command_kind",
    "--pull=false",
    "--network=none",
    "--load",
    "--pull",
    "never",
    "127.0.0.1",
    "no-new-privileges",
    "cap-drop",
)
for marker in required_runner_markers:
    if marker not in runner_text:
        raise SystemExit(f"runner policy marker missing: {marker}")
for marker in ("shell=True", "os.system", "docker login", "docker pull", "docker push", "docker system prune"):
    if marker in runner_text:
        raise SystemExit(f"runner contains prohibited execution marker: {marker}")

spec = importlib.util.spec_from_file_location("aion241_runner_no_go", runner_path)
if spec is None or spec.loader is None:
    raise SystemExit("unable to load AION-241 runner")
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)
docker = "/usr/local/bin/docker"
module.assert_allowed_docker_command(
    docker,
    [
        docker,
        "buildx",
        "build",
        "--load",
        "--pull=false",
        "--network=none",
        "--file",
        "Dockerfile",
        "--tag",
        "aion241:test",
        "context",
    ],
)
for command in (
    [docker, "login"],
    [docker, "pull", "redis:7-alpine"],
    [docker, "push", "aion241:test"],
    [docker, "run", "--rm", "--privileged", "image"],
    [docker, "run", "--rm", "--network", "host", "image"],
    [docker, "system", "prune"],
):
    try:
        module.assert_allowed_docker_command(docker, command)
    except RuntimeError:
        continue
    raise SystemExit(f"runner allowed prohibited Docker command: {command}")

for ledger_path in (
    root / "docs/v02-release-qualification/program-ledger.json",
    root / "docs/v02-release-qualification/authorization-ledger.json",
    root / "examples/v02-release-qualification/staging-qualification-authorization.json",
):
    payload = json.loads(ledger_path.read_text(encoding="utf-8"))
    for key, value in payload.get("prohibited_capabilities", {}).items():
        if value is not False:
            raise SystemExit(f"{ledger_path} enabled prohibited capability: {key}")
    for key in payload.get("zero_resource_limit_keys", []):
        if payload.get("resource_limits", {}).get(key) != 0:
            raise SystemExit(f"{ledger_path} zero resource limit mismatch: {key}")
    for key in (
        "production_runtime_authorized",
        "production_deployment_enabled",
        "release_candidate_creation_enabled",
        "v02_release_ready",
        "v02_tag_created",
        "v02_release_created",
    ):
        if payload.get(key) is not False:
            raise SystemExit(f"{ledger_path} must keep {key}=false")
PY

aion_confirm_immutable_v01_tag_history >/dev/null
if git tag --list 'v0.2*' 'aion-v0.2*' | rg -n '.+' >/dev/null 2>&1; then
  echo "AION-241 must not create a v0.2 tag" >&2
  exit 1
fi
if command -v gh >/dev/null 2>&1; then
  if gh release view v0.2 >/dev/null 2>&1 || gh release view aion-v0.2 >/dev/null 2>&1; then
    echo "AION-241 must not create a v0.2 release" >&2
    exit 1
  fi
fi

echo "controlled isolated staging qualification no-go PASS"
