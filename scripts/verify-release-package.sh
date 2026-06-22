#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RELEASE_DIR="${1:-${ROOT_DIR}/artifacts/releases}"

python3 - "$RELEASE_DIR" <<'PY'
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

release_dir = Path(sys.argv[1])
if not release_dir.exists():
    print(f"release directory not found: {release_dir}", file=sys.stderr)
    raise SystemExit(1)

manifests = sorted(release_dir.rglob("release-package-manifest.json"))
if not manifests:
    print("release-package-manifest.json not found", file=sys.stderr)
    raise SystemExit(1)

manifest_path = manifests[-1]
package_dir = manifest_path.parent
checksums_path = package_dir / "checksums.json"
if not checksums_path.exists():
    print("checksums.json not found", file=sys.stderr)
    raise SystemExit(1)

manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
checksums = json.loads(checksums_path.read_text(encoding="utf-8"))
if not isinstance(checksums, dict):
    print("checksums.json must contain an object", file=sys.stderr)
    raise SystemExit(1)

failures: list[str] = []
for relative, expected in checksums.items():
    if not isinstance(relative, str) or not isinstance(expected, str):
        failures.append(str(relative))
        continue
    candidate = package_dir / relative
    if not candidate.exists():
        candidate = package_dir / "generated" / Path(relative).name
    if not candidate.exists():
        continue
    actual = hashlib.sha256(candidate.read_bytes()).hexdigest()
    if actual != expected:
        failures.append(relative)

if failures:
    print(f"checksum verification failed: {failures}", file=sys.stderr)
    raise SystemExit(1)

print(
    json.dumps(
        {
            "verified": True,
            "package_dir": package_dir.as_posix(),
            "package_name": manifest.get("package_name"),
            "file_count": manifest.get("file_count"),
        },
        sort_keys=True,
    )
)
PY
