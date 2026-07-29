#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/immutable-tags.sh"
source "$ROOT_DIR/scripts/lib/portable-search.sh"
source "$ROOT_DIR/scripts/lib/python-selection.sh"
PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"

git_ref_exists() {
  git rev-parse --verify --quiet "$1" >/dev/null 2>&1
}

comparison_base() {
  local candidate merge_base
  if [[ -n "${GITHUB_BASE_REF:-}" ]]; then
    for candidate in "origin/${GITHUB_BASE_REF}" "${GITHUB_BASE_REF}"; do
      if git_ref_exists "$candidate"; then
        merge_base="$(git merge-base HEAD "$candidate" 2>/dev/null || true)"
        [[ -n "$merge_base" ]] && { echo "$merge_base"; return 0; }
      fi
    done
  fi
  for candidate in origin/main main; do
    if git_ref_exists "$candidate"; then
      merge_base="$(git merge-base HEAD "$candidate" 2>/dev/null || true)"
      [[ -n "$merge_base" ]] && { echo "$merge_base"; return 0; }
    fi
  done
  git_ref_exists HEAD~1 && { echo HEAD~1; return 0; }
  return 1
}

if git ls-files '*.db' '*.sqlite' '*.sqlite3' '*-wal' '*-shm' '*.sqlite3-wal' '*.sqlite3-shm' | rg -n '.+'; then
  echo "ERROR: tracked SQLite/database runtime file exists" >&2
  exit 1
fi

if base="$(comparison_base)"; then
  if git diff --name-only "$base" HEAD -- .github/workflows package.json package-lock.json pnpm-lock.yaml yarn.lock bun.lockb poetry.lock uv.lock Pipfile Pipfile.lock migrations services/brain-api/migrations infra/postgres/migrations | rg -n '.+'; then
    echo "ERROR: dependency, workflow, or migration surface changed" >&2
    exit 1
  fi
else
  echo "WARN: comparison base unavailable; skipping dependency/workflow/migration diff confirmation" >&2
fi

"$PYTHON_BIN" - <<'PY'
from __future__ import annotations

import json
import re
from pathlib import Path

root = Path.cwd()
state = json.loads((root / "docs/governed-learning-memory/program-ledger.json").read_text())
implemented_states = {
    "governed_learning_memory_local_append_only_persistence_implemented_operator_invoked_isolated_pending_closeout",
    "governed_learning_memory_engagement_application_authorized_not_implemented",
    "governed_learning_memory_engagement_application_implemented_shadow_only_pending_closeout",
}
if state.get("program_state") not in implemented_states:
    raise SystemExit("ERROR: AION-224 implemented state missing")
for key in (
    "general_persistent_knowledge_write_enabled",
    "background_persistent_knowledge_write_enabled",
    "scheduled_persistent_knowledge_write_enabled",
    "production_persistent_knowledge_write_enabled",
    "existing_memory_repository_write_enabled",
    "production_memory_repository_write_enabled",
    "actual_belief_creation_enabled",
    "actual_belief_mutation_enabled",
    "belief_repository_write_enabled",
    "automatic_candidate_approval_enabled",
    "automatic_knowledge_promotion_enabled",
    "automatic_memory_ingestion_enabled",
    "automatic_engagement_learning_application_enabled",
    "network_access_enabled",
    "runtime_enabled",
    "production_exposure",
    "v02_release_ready",
    "v02_tag_created",
    "v02_release_created",
):
    if state.get(key) is not False:
        raise SystemExit(f"ERROR: prohibited flag enabled: {key}")

source_paths = [
    "services/brain-api/src/aion_brain/contracts/governed_learning_memory_persistence.py",
    "services/brain-api/src/aion_brain/governed_learning_memory/local_persistence_policy.py",
    "services/brain-api/src/aion_brain/governed_learning_memory/local_sqlite_schema.py",
    "services/brain-api/src/aion_brain/governed_learning_memory/local_sqlite_store.py",
    "services/brain-api/src/aion_brain/governed_learning_memory/persistence_approval.py",
    "services/brain-api/src/aion_brain/governed_learning_memory/knowledge_content.py",
    "services/brain-api/src/aion_brain/governed_learning_memory/knowledge_persistence.py",
    "services/brain-api/src/aion_brain/governed_learning_memory/memory_projection_persistence.py",
    "services/brain-api/src/aion_brain/governed_learning_memory/persistence_transactions.py",
    "services/brain-api/src/aion_brain/governed_learning_memory/persistence_integrity.py",
    "services/brain-api/src/aion_brain/governed_learning_memory/backup_restore.py",
    "services/brain-api/src/aion_brain/governed_learning_memory/persistence_evidence.py",
]
for rel in source_paths:
    if not (root / rel).exists():
        raise SystemExit(f"ERROR: missing AION-224 source file: {rel}")

sqlite_allowed = {
    "services/brain-api/src/aion_brain/governed_learning_memory/local_sqlite_store.py",
    "scripts/governed-learning-memory-local-persistence-run.py",
}
runtime_paths = [*source_paths, "scripts/governed-learning-memory-local-persistence-run.py"]
prohibited_patterns = {
    "MemoryRepository": "MemoryRepository import or call",
    "ApprovalService": "ApprovalService import or call",
    "ApprovalRepository": "ApprovalRepository import or call",
    "BeliefRepository": "belief repository import or call",
    "BeliefClaim": "BeliefClaim creation or mutation",
    "create_belief(": "belief creation primitive",
    "persist_knowledge(": "production knowledge write primitive",
    "subprocess": "subprocess execution",
    "socket": "network primitive",
    "requests" + ".": "network primitive",
    "httpx" + ".": "network primitive",
    "aiohttp" + ".": "network primitive",
    "urllib" + ".request": "network primitive",
    "playwright": "browser automation",
    "selenium": "browser automation",
    "ApprovalRequest(": "approval creation",
    "ApprovalDecision(": "approval decision creation",
}
for rel in runtime_paths:
    text = (root / rel).read_text(encoding="utf-8")
    if "sqlite3" in text and rel not in sqlite_allowed:
        raise SystemExit(f"ERROR: sqlite3 used outside allowed local store/runner: {rel}")
    for needle, label in prohibited_patterns.items():
        if needle in text:
            raise SystemExit(f"ERROR: {label}: {rel}")
    if re.search(r"operator_sql|raw_sql|arbitrary_sql|execute_sql|sql_text|sql_statement|ATTACH DATABASE|DETACH DATABASE", text, re.I):
        raise SystemExit(f"ERROR: arbitrary SQL surface detected: {rel}")
    if "executescript(" in text and "CREATE_SCHEMA_SQL" not in text:
        raise SystemExit(f"ERROR: non-static executescript use: {rel}")

pilot = json.loads((root / "examples/governed-learning-memory/local-persistence-synthetic-pilot-evidence.json").read_text())
if pilot.get("temporary_database_files_retained") != 0:
    raise SystemExit("ERROR: pilot retained database files")
if pilot.get("actual_beliefs_created") != 0 or pilot.get("production_memory_writes") != 0:
    raise SystemExit("ERROR: pilot reports prohibited side effect")
PY

if git tag --list 'v0.2*' 'aion-v0.2*' | rg -n '.+'; then
  echo "ERROR: v0.2 tag exists" >&2
  exit 1
fi
if command -v gh >/dev/null 2>&1; then
  if gh release view v0.2 >/dev/null 2>&1 || gh release view aion-v0.2 >/dev/null 2>&1; then
    echo "ERROR: v0.2 release exists" >&2
    exit 1
  fi
fi
aion_confirm_immutable_v01_tag_history >/dev/null
echo "governed learning memory local persistence no-go PASS"
