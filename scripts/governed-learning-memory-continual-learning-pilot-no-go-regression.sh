#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/immutable-tags.sh"
source "$ROOT_DIR/scripts/lib/portable-search.sh"

if git ls-files '*.db' '*.sqlite' '*.sqlite3' '*-wal' '*-shm' '*.backup' '*.state' | rg -n '.+'; then
  echo "ERROR: tracked database, WAL, SHM, backup, or state artifact exists" >&2
  exit 1
fi

if git rev-parse --verify --quiet origin/main >/dev/null 2>&1; then
  changed="$(git diff --name-only "$(git merge-base HEAD origin/main)" HEAD)"
else
  changed=""
fi
if printf '%s\n' "$changed" | rg -n '^\.github/workflows/|^services/brain-api/pyproject\.toml$|^packages/aion-sdk-python/src/|^migrations/|^(package|package-lock|pnpm-lock|yarn)\.json$|^bun\.lockb$'; then
  echo "ERROR: AION-228 changed workflow, dependency, SDK, package, or migration surface" >&2
  exit 1
fi

allowed='^(services/brain-api/src/aion_brain/contracts/governed_continual_learning\.py|services/brain-api/src/aion_brain/governed_learning_memory/continual_learning_[a-z_]+\.py|services/brain-api/src/aion_brain/governed_learning_memory/__init__\.py|scripts/governed-learning-memory-controlled-local-continual-learning-run\.py)$'
if printf '%s\n' "$changed" | rg 'continual_learning|continual-learning.*run\.py' | rg -v "$allowed"; then
  echo "ERROR: unexpected continual-learning source path exists" >&2
  exit 1
fi

if rg -n \
  '(import socket|import ssl|import http\.client|import requests|import httpx|import aiohttp|urllib\.request|ApprovalService|ApprovalRepository|MemoryRepository|belief repository|background_worker|scheduler|automatic_cycle_continuation.*True|production_memory_write.*True|production_policy_mutation.*True|source_mutation.*True|git_mutation.*True)' \
  services/brain-api/src/aion_brain/contracts/governed_continual_learning.py \
  services/brain-api/src/aion_brain/governed_learning_memory/continual_learning_*.py \
  scripts/governed-learning-memory-controlled-local-continual-learning-run.py; then
  echo "ERROR: prohibited AION-228 runtime surface detected" >&2
  exit 1
fi

if rg -n \
  '(background_continual_learning_enabled": true|scheduled_continual_learning_enabled": true|automatic_knowledge_promotion_enabled": true|automatic_candidate_approval_enabled": true|production_memory_writes": [1-9]|production_policy_mutations": [1-9]|actual_belief_creations": [1-9]|actual_belief_mutations": [1-9]|source_mutations": [1-9]|git_operations": [1-9]|production_exposure": true|v02_release_ready": true)' \
  docs/governed-learning-memory docs/release examples/governed-learning-memory operator-console-static/demo-data; then
  echo "ERROR: AION-228 zero-effect boundary violated" >&2
  exit 1
fi

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

echo "governed learning memory continual learning pilot no-go PASS"
