#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
status=0

fail() {
  echo "FAIL: $1"
  status=1
}

pass() {
  echo "PASS: $1"
}

for path in README.md AGENTS.md docker-compose.yml services/brain-api packages/aion-sdk-python docs/adr; do
  if [[ -e "$ROOT_DIR/$path" ]]; then
    pass "$path exists"
  else
    fail "$path is missing"
  fi
done

while IFS= read -r file; do
  [[ -s "$file" ]] || fail "empty docs file: ${file#$ROOT_DIR/}"
done < <(find "$ROOT_DIR/docs" -type f -name '*.md' 2>/dev/null)

while IFS= read -r script; do
  [[ -x "$script" ]] || fail "script is not executable: ${script#$ROOT_DIR/}"
done < <(find "$ROOT_DIR/scripts" -maxdepth 1 -type f -name '*.sh')

for cache in __pycache__ .pytest_cache .mypy_cache .ruff_cache .aion_objects .aion_indexes; do
  if git -C "$ROOT_DIR" ls-files | grep -E "(^|/)${cache}(/|$)" >/dev/null; then
    fail "generated cache/object directory is tracked: $cache"
  else
    pass "no tracked $cache directory"
  fi
done

if git -C "$ROOT_DIR" ls-files | grep -E '(^|/)\.env$' >/dev/null; then
  fail ".env file is tracked"
else
  pass "no tracked .env file"
fi

while IFS= read -r file; do
  if [[ -f "$ROOT_DIR/$file" ]]; then
    size=$(wc -c < "$ROOT_DIR/$file")
    if [[ "$size" -gt 10485760 ]]; then
      fail "tracked file larger than 10MB: $file"
    fi
  fi
done < <(git -C "$ROOT_DIR" ls-files)

if [[ "$status" -eq 0 ]]; then
  echo "Repository health PASS"
else
  echo "Repository health FAIL"
fi
exit "$status"
