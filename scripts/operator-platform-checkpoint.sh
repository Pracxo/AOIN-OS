#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

checks=(
  ./scripts/ui-release-gate.sh
  ./scripts/static-console-safety-check.sh
  ./scripts/operator-console-static-check.sh
  ./scripts/auth-runtime-check.sh
  ./scripts/action-authorization-check.sh
  ./scripts/role-filter-check.sh
  ./scripts/local-session-check.sh
  ./scripts/local-auth-check.sh
  ./scripts/docs-check.sh
  ./scripts/final-docs-audit.sh
  ./scripts/verify-no-domain-drift.sh
  ./scripts/boundary-check.sh
)

for check in "${checks[@]}"; do
  "$check"
done

required_files=(
  docs/operator-console/operator-platform-phase-checkpoint.md
  docs/operator-console/operator-platform-evidence-pack.md
  docs/operator-console/operator-platform-risk-register.md
  docs/operator-console/operator-platform-next-phase.md
  docs/operator-console/operator-platform-release-readiness.md
  docs/operator-console/operator-platform-checkpoint.md
  docs/adr/0092-operator-platform-checkpoint.md
  examples/operator-console/operator-platform-checkpoint.json
  examples/operator-console/operator-platform-evidence-pack.json
  examples/operator-console/operator-platform-risk-register.json
)

for file in "${required_files[@]}"; do
  test -f "$file" || {
    echo "missing operator platform checkpoint artifact: $file" >&2
    exit 1
  }
done

grep -q "0092-operator-platform-checkpoint.md" docs/adr/README.md || {
  echo "ADR 0092 is not indexed" >&2
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
    example_dir / "operator-platform-checkpoint.json",
    example_dir / "operator-platform-evidence-pack.json",
    example_dir / "operator-platform-risk-register.json",
]

for path in examples:
    json.loads(path.read_text())

checkpoint = json.loads((example_dir / "operator-platform-checkpoint.json").read_text())
if checkpoint.get("status") != "passed":
    raise SystemExit("operator platform checkpoint status must be passed")
for key in ("read_only", "local_only"):
    if checkpoint.get(key) is not True:
        raise SystemExit(f"{key} must be true")
for key in (
    "production_auth_enabled",
    "external_calls_enabled",
    "activation_enabled",
    "execution_enabled",
    "frontend_dependencies_present",
    "build_system_present",
):
    if checkpoint.get(key) is not False:
        raise SystemExit(f"{key} must be false")

required_tasks = {f"AION-{number:03d}" for number in range(89, 101)}
if set(checkpoint.get("covered_tasks", [])) != required_tasks:
    raise SystemExit("checkpoint covered_tasks must include AION-089 through AION-100")

evidence_pack = json.loads((example_dir / "operator-platform-evidence-pack.json").read_text())
areas = {item.get("area") for item in evidence_pack.get("evidence", [])}
required_areas = {
    "Static console safety",
    "Module lifecycle dashboard",
    "Provider dashboard",
    "Operator actions",
    "Local auth",
    "Local session",
    "Role filtering",
    "Action authorization",
    "Production auth architecture",
    "Disabled auth prototype",
    "UI release gate",
    "Docs audit",
    "Boundary check",
    "Repository health",
}
missing_areas = sorted(required_areas - areas)
if missing_areas:
    raise SystemExit(f"operator platform evidence missing areas: {missing_areas}")
for item in evidence_pack.get("evidence", []):
    if item.get("expected_status") != "passed":
        raise SystemExit(f"evidence item must expect passed: {item}")
    script = item.get("script")
    if not isinstance(script, str) or not script.startswith("./scripts/"):
        raise SystemExit(f"evidence item must use a local script: {item}")

risk_pack = json.loads((example_dir / "operator-platform-risk-register.json").read_text())
risks = {item.get("risk") for item in risk_pack.get("risks", [])}
required_risks = {
    "frontend dependency creep",
    "hidden write action",
    "activation leakage",
    "auth runtime enablement",
    "credential/session storage",
    "raw prompt exposure",
    "hidden reasoning exposure",
    "provider call leakage",
    "external URL call",
    "stale demo data",
    "policy bypass",
    "audit bypass",
}
missing_risks = sorted(required_risks - risks)
if missing_risks:
    raise SystemExit(f"operator platform risk register missing risks: {missing_risks}")
for item in risk_pack.get("risks", []):
    if not item.get("control") or not item.get("no_go_condition"):
        raise SystemExit(f"risk item missing control or no_go_condition: {item}")

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
try:
    base = subprocess.run(
        ["git", "merge-base", "HEAD", "main"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
except subprocess.CalledProcessError:
    base = ""
if base:
    changed |= git_lines("diff", "--name-only", "--diff-filter=ACMRT", f"{base}..HEAD", "--")

aion108_allowed_files = {
    "services/brain-api/src/aion_brain/api/connector_runtime.py",
    "services/brain-api/src/aion_brain/api/connector_simulator.py",
    "services/brain-api/src/aion_brain/api/connector_policy.py",
    "services/brain-api/src/aion_brain/api/connector_sandbox.py",
}
for relative in sorted(changed):
    if relative in aion108_allowed_files:
        continue
    parts = set(Path(relative).parts)
    if "migrations" in parts:
        raise SystemExit(f"AION-101 must not add a migration: {relative}")
    if relative.startswith("services/brain-api/src/aion_brain/api/"):
        raise SystemExit(f"AION-101 must not add an API router file: {relative}")
    if "/routers/" in relative or relative.endswith("_router.py"):
        raise SystemExit(f"AION-101 must not add an API router file: {relative}")

checkpoint_docs = [
    root / "docs/operator-console/operator-platform-phase-checkpoint.md",
    root / "docs/operator-console/operator-platform-evidence-pack.md",
    root / "docs/operator-console/operator-platform-risk-register.md",
    root / "docs/operator-console/operator-platform-next-phase.md",
    root / "docs/operator-console/operator-platform-release-readiness.md",
    root / "docs/adr/0092-operator-platform-checkpoint.md",
]
for path in checkpoint_docs:
    lowered = path.read_text().lower()
    if "production ready" in lowered or "production-ready" in lowered:
        raise SystemExit(f"production UI readiness claim found: {path}")
    if "http://" in lowered or "https://" in lowered:
        raise SystemExit(f"external URL found in checkpoint doc: {path}")

print("Operator platform checkpoint examples PASS")
print("Operator platform dependency and route guard PASS")
PY

cat <<'SUMMARY'
Operator platform checkpoint summary:
- static_console_safe: true
- operator_platform_read_only: true
- production_auth_enabled: false
- frontend_dependencies_present: false
- write_activation_execution_provider_external_controls_absent: true
Operator platform checkpoint PASS
SUMMARY
