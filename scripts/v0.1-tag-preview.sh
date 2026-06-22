#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

echo "AION Brain v0.1.0 tag preview"
echo
echo "Current worktree:"
git status --short
if [[ -n "$(git status --short)" ]]; then
  echo "WARNING: worktree has changes. Do not tag until final verification is green and the release baseline commit exists."
fi
echo
echo "Latest commit:"
git log -1 --oneline
echo
echo "Exact local tag preparation commands:"
cat <<'EOF'
git status --short
git log -1 --oneline
./scripts/v0.1-final-verify.sh
git tag aion-v0.1.0
git show --stat aion-v0.1.0
EOF
echo
echo "This preview does not create a tag, push, publish, deploy, or call external services."
