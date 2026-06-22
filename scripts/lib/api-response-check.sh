#!/usr/bin/env bash

aion_assert_api_response_ok() {
  local label="$1"
  local response_file="$2"

  python3 - "$label" "$response_file" <<'PY'
import json
import sys
from pathlib import Path

label = sys.argv[1]
path = Path(sys.argv[2])

try:
    text = path.read_text(encoding="utf-8")
except OSError as exc:
    print(f"{label}: cannot read API response: {exc}", file=sys.stderr)
    sys.exit(1)

if not text.strip():
    print(f"{label}: empty API response", file=sys.stderr)
    sys.exit(1)

try:
    payload = json.loads(text)
except json.JSONDecodeError as exc:
    print(f"{label}: invalid JSON response: {exc}", file=sys.stderr)
    sys.exit(1)

failures: list[str] = []


def _as_int(value: object) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.strip().isdigit():
        return int(value)
    return None


def visit(value: object, trail: str) -> None:
    if isinstance(value, dict):
        status = value.get("status")
        if isinstance(status, str) and status.lower() == "failed":
            failures.append(f"{trail}.status=failed")

        validation = value.get("validation")
        if isinstance(validation, dict):
            validation_status = validation.get("status")
            if isinstance(validation_status, str) and validation_status.lower() == "failed":
                failures.append(f"{trail}.validation.status=failed")

        if value.get("release_ready") is False:
            failures.append(f"{trail}.release_ready=false")

        blocker_count = _as_int(value.get("blocker_count"))
        if blocker_count is not None and blocker_count > 0:
            failures.append(f"{trail}.blocker_count={blocker_count}")

        for key, child in value.items():
            if key == "evidence":
                continue
            visit(child, f"{trail}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            visit(child, f"{trail}[{index}]")


visit(payload, "$")

if failures:
    print(f"{label}: API response reports failed release gate semantics", file=sys.stderr)
    for failure in failures:
        print(f"  - {failure}", file=sys.stderr)
    sys.exit(1)
PY
}
