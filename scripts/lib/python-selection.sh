#!/usr/bin/env bash

aion_repo_root() {
  if [[ -n "${ROOT_DIR:-}" ]]; then
    printf '%s\n' "$ROOT_DIR"
    return 0
  fi

  git rev-parse --show-toplevel 2>/dev/null || pwd
}

aion_select_brain_python() {
  local repo_root="${1:-$(aion_repo_root)}"

  if [[ -n "${AION_BRAIN_PYTHON:-}" ]]; then
    if [[ -x "$AION_BRAIN_PYTHON" && ! -d "$AION_BRAIN_PYTHON" ]]; then
      printf '%s\n' "$AION_BRAIN_PYTHON"
      return 0
    fi
    echo "AION_BRAIN_PYTHON is set but is not an executable file: $AION_BRAIN_PYTHON" >&2
    return 1
  fi

  if [[ -x "$repo_root/services/brain-api/.venv/bin/python" ]]; then
    printf '%s\n' "$repo_root/services/brain-api/.venv/bin/python"
    return 0
  fi

  if command -v python3 >/dev/null 2>&1; then
    command -v python3
    return 0
  fi

  if command -v python >/dev/null 2>&1; then
    command -v python
    return 0
  fi

  echo "No Python interpreter found; set AION_BRAIN_PYTHON or install python3/python" >&2
  return 1
}

aion_verify_brain_python_test_dependencies() {
  local python_bin="$1"

  if "$python_bin" -c 'import pytest, pydantic' >/dev/null 2>&1; then
    return 0
  fi

  echo "Selected Python interpreter cannot import required modules: pytest, pydantic ($python_bin)" >&2
  return 1
}
