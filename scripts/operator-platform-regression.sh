#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

checks=(
  ./scripts/operator-platform-checkpoint.sh
  ./scripts/ui-release-gate.sh
  ./scripts/static-console-safety-check.sh
  ./scripts/operator-console-static-check.sh
  ./scripts/module-lifecycle-dashboard-check.sh
  ./scripts/provider-dashboard-check.sh
  ./scripts/operator-actions-check.sh
  ./scripts/action-authorization-check.sh
  ./scripts/auth-runtime-check.sh
  ./scripts/production-auth-architecture-check.sh
  ./scripts/local-auth-check.sh
  ./scripts/local-session-check.sh
  ./scripts/role-filter-check.sh
  ./scripts/docs-check.sh
  ./scripts/final-docs-audit.sh
  ./scripts/verify-no-domain-drift.sh
  ./scripts/boundary-check.sh
  ./scripts/check.sh
)

for check in "${checks[@]}"; do
  "$check"
done

required_files=(
  docs/operator-console/operator-platform-regression-matrix.md
  docs/operator-console/operator-platform-freeze-gate.md
  docs/operator-console/operator-platform-long-running-checks.md
  docs/operator-console/operator-platform-stabilization-runbook.md
  docs/operator-console/operator-platform-regression-evidence.md
  docs/adr/0093-operator-platform-stabilization-gate.md
  examples/operator-console/operator-platform-regression-matrix.json
  examples/operator-console/operator-platform-freeze-gate-result.json
  examples/operator-console/operator-platform-regression-evidence.json
)

for file in "${required_files[@]}"; do
  test -f "$file" || {
    echo "missing operator platform regression artifact: $file" >&2
    exit 1
  }
done

grep -q "0093-operator-platform-stabilization-gate.md" docs/adr/README.md || {
  echo "ADR 0093 is not indexed" >&2
  exit 1
}

python3 - "$ROOT_DIR" <<'PY'
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

root = Path(sys.argv[1])
example_dir = root / "examples/operator-console"
examples = [
    example_dir / "operator-platform-regression-matrix.json",
    example_dir / "operator-platform-freeze-gate-result.json",
    example_dir / "operator-platform-regression-evidence.json",
]

for path in examples:
    payload = json.loads(path.read_text())
    serialized = json.dumps(payload, sort_keys=True).lower()
    for marker in (
        "raw_prompt",
        "hidden_reasoning",
        "chain_of_thought",
        "password",
        "api_key",
        "private_key",
        "bearer ",
        "sk-",
        "ghp_",
        "xoxb-",
    ):
        if marker in serialized:
            raise SystemExit(f"unsafe operator platform regression example marker in {path}: {marker}")

matrix = json.loads((example_dir / "operator-platform-regression-matrix.json").read_text())
required_areas = {
    "static console safety",
    "UI release gate",
    "module lifecycle dashboard",
    "provider hardening dashboard",
    "operator actions",
    "action authorization",
    "local auth",
    "local session",
    "role filtering",
    "production auth architecture",
    "disabled auth runtime",
    "docs audit",
    "boundary check",
    "repository health",
}
areas = {row.get("area") for row in matrix.get("areas", [])}
missing = sorted(required_areas - areas)
if missing:
    raise SystemExit(f"regression matrix missing areas: {missing}")
for row in matrix.get("areas", []):
    if row.get("expected_status") != "passed":
        raise SystemExit(f"regression row must expect passed: {row}")
    if row.get("release_blocker") is not True:
        raise SystemExit(f"regression row must be a release blocker: {row}")
    script = row.get("script")
    if not isinstance(script, str) or not script.startswith("./scripts/"):
        raise SystemExit(f"regression row must use local script: {row}")

freeze = json.loads((example_dir / "operator-platform-freeze-gate-result.json").read_text())
if freeze.get("status") != "passed":
    raise SystemExit("freeze gate result must be passed")
safety_flags = freeze.get("safety_flags", {})
if safety_flags.get("static_console_read_only") is not True:
    raise SystemExit("static_console_read_only must be true")
for key in (
    "auth_runtime_enabled",
    "production_auth_enabled",
    "write_controls_present",
    "activation_controls_present",
    "execution_controls_present",
    "provider_call_controls_present",
    "external_calls_enabled",
    "frontend_dependencies_present",
    "package_install_allowed",
):
    if safety_flags.get(key) is not False:
        raise SystemExit(f"{key} must be false")

evidence = json.loads((example_dir / "operator-platform-regression-evidence.json").read_text())
if evidence.get("status") != "passed":
    raise SystemExit("regression evidence must be passed")
for row in evidence.get("evidence", []):
    if row.get("expected_status") != "passed":
        raise SystemExit(f"evidence row must expect passed: {row}")
    script = row.get("script")
    if not isinstance(script, str) or not script.startswith("./scripts/"):
        raise SystemExit(f"evidence row must use local script: {row}")

blocked_names = {
    "package.json",
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "bun.lockb",
}
blocked_prefixes = (
    "vite.config.",
    "next.config.",
    "tailwind.config.",
    "webpack.config.",
)
skip_parts = {
    ".git",
    ".venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
}
for path in root.rglob("*"):
    if not path.is_file() or any(part in skip_parts for part in path.parts):
        continue
    name = path.name
    if name in blocked_names or any(name.startswith(prefix) for prefix in blocked_prefixes):
        raise SystemExit(f"frontend package or build file is not allowed: {path}")


def git_lines(*args: str) -> set[str]:
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    return {line.strip() for line in result.stdout.splitlines() if line.strip()}


changed: set[str] = set()
changed |= git_lines("diff", "--name-only", "--diff-filter=ACMRT", "HEAD", "--")
changed |= git_lines("diff", "--cached", "--name-only", "--diff-filter=ACMRT", "--")
changed |= git_lines("ls-files", "--others", "--exclude-standard")
for ref in ("origin/main", "main"):
    merge_base = subprocess.run(
        ["git", "merge-base", "HEAD", ref],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    if merge_base.returncode == 0 and merge_base.stdout.strip():
        changed |= git_lines(
            "diff",
            "--name-only",
            "--diff-filter=ACMRT",
            f"{merge_base.stdout.strip()}..HEAD",
            "--",
        )
        break

for relative in sorted(changed):
    parts = set(Path(relative).parts)
    if "migrations" in parts:
        raise SystemExit(f"AION-102 must not add a migration: {relative}")
    if relative.startswith("services/brain-api/src/aion_brain/api/"):
        raise SystemExit(f"AION-102 must not add an API router file: {relative}")
    if "/routers/" in relative or relative.endswith("_router.py"):
        raise SystemExit(f"AION-102 must not add an API router file: {relative}")

print("Operator platform regression examples PASS")
print("Operator platform regression dependency and route guard PASS")
PY

cat <<'SUMMARY'
Operator platform regression summary:
- checkpoint_gate: passed
- static_console_regression: passed
- auth_safety_regression: passed
- operator_action_regression: passed
- module_provider_dashboard_regression: passed
- full_repository_check: passed
Operator platform regression PASS
SUMMARY
