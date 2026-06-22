#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
MIGRATIONS_DIR="$ROOT_DIR/infra/postgres/migrations"

"${PYTHON:-python3}" - "$MIGRATIONS_DIR" <<'PY'
from __future__ import annotations

import re
import sys
from collections import Counter
from pathlib import Path

migrations_dir = Path(sys.argv[1])
violations: list[str] = []

if not migrations_dir.exists():
    violations.append("migrations directory is missing")
else:
    files = sorted(migrations_dir.glob("*.py"))
    if not files:
        violations.append("migrations directory has no migration files")
    names = [path.name for path in files]
    for name, count in Counter(names).items():
        if count > 1:
            violations.append(f"duplicate migration filename: {name}")
    table_pattern = re.compile(r'Table\(\s*["\']([^"\']+)["\']')
    for path in files:
        text = path.read_text(encoding="utf-8")
        if not text.strip():
            violations.append(f"{path.name}: migration file is empty")
        if "DROP TABLE" in text.upper() and "AION_ALLOW_DESTRUCTIVE_MIGRATION" not in text:
            violations.append(f"{path.name}: destructive DROP TABLE without allow comment")
        tables = table_pattern.findall(text)
        for table, count in Counter(tables).items():
            if count > 1:
                violations.append(f"{path.name}: duplicate table creation for {table}")

if violations:
    print("Migration check FAIL")
    for item in violations:
        print(item)
    sys.exit(1)

print("Migration check PASS")
PY
