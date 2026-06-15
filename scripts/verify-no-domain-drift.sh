#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

"${PYTHON:-python3}" - "$ROOT_DIR" <<'PY'
from __future__ import annotations

import re
import sys
from pathlib import Path

root = Path(sys.argv[1])
forbidden = (
    "finance",
    "trading",
    "legal",
    "healthcare",
    "medical",
    "hr",
    "procurement",
    "payments",
    "crm",
    "erp",
)
route_prefixes = (
    "/finance",
    "/trading",
    "/legal",
    "/healthcare",
    "/medical",
    "/hr",
    "/procurement",
)
module_patterns = tuple(re.compile(rf"\b{name}\.[a-z0-9_]+\b") for name in forbidden)
violations: list[str] = []

source_root = root / "services" / "brain-api" / "src" / "aion_brain"
if source_root.exists():
    for path in source_root.rglob("*"):
        if path.is_dir() and path.name.lower() in forbidden:
            violations.append(f"{path.relative_to(root)}: forbidden domain directory")

allowed_doc_context = (
    "no ",
    "not ",
    "without",
    "forbidden",
    "exclude",
    "exclusion",
    "domain",
    "vertical",
    "must not",
    "disabled",
    "outside brain core",
)
allowed_paths = {"README.md", "AGENTS.md"}
scan_roots = [
    root / "services" / "brain-api" / "src",
    root / "packages",
    root / "examples",
    root / "docs",
]

def should_skip_file(path: Path) -> bool:
    parts = set(path.parts)
    if path.name == "openapi_hygiene.py":
        return True
    return bool(
        parts.intersection(
            {".git", ".venv", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"}
        )
    )

def doc_line_allowed(relative: str, line: str) -> bool:
    lowered = line.lower()
    return relative in allowed_paths or any(token in lowered for token in allowed_doc_context)

for scan_root in scan_roots:
    if not scan_root.exists():
        continue
    for path in scan_root.rglob("*"):
        if not path.is_file() or should_skip_file(path):
            continue
        if path.suffix not in {".py", ".md", ".yaml", ".yml", ".json", ".toml", ".txt"}:
            continue
        relative = path.relative_to(root).as_posix()
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            continue
        for lineno, line in enumerate(lines, start=1):
            lowered = line.lower()
            if path.suffix == ".md" and doc_line_allowed(relative, line):
                continue
            if any(prefix in lowered for prefix in route_prefixes):
                violations.append(f"{relative}:{lineno}: forbidden route prefix")
            if "examples/" in relative:
                for pattern in module_patterns:
                    if pattern.search(lowered):
                        violations.append(f"{relative}:{lineno}: forbidden domain module id")

if violations:
    print("No-domain-drift FAIL")
    for item in violations:
        print(item)
    sys.exit(1)

print("No-domain-drift PASS")
PY
