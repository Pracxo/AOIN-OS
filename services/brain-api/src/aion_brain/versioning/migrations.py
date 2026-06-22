"""Migration baseline service."""

from __future__ import annotations

import hashlib
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast
from uuid import uuid4

from aion_brain.api_support.errors import AIONPolicyDeniedException
from aion_brain.config import Settings, get_settings
from aion_brain.contracts.compatibility import MigrationBaseline
from aion_brain.contracts.policy import PolicyRequest
from aion_brain.policy.base import PolicyAdapter
from aion_brain.policy.enrichment import enrich_with_internal_dev_actor
from aion_brain.versioning.compatibility import emit_versioning_telemetry
from aion_brain.versioning.repository import VersioningRepository

DESTRUCTIVE_OVERRIDE = "AION_ALLOW_DESTRUCTIVE_MIGRATION"
_DESTRUCTIVE_PATTERNS = (
    re.compile(r"\bDROP\s+TABLE\b", re.IGNORECASE),
    re.compile(r"\bDROP\s+COLUMN\b", re.IGNORECASE),
    re.compile(r"\bTRUNCATE\b", re.IGNORECASE),
    re.compile(r"\bDELETE\s+FROM\b(?![^;]*\bWHERE\b)", re.IGNORECASE | re.DOTALL),
    re.compile(r"\bop\.drop_table\s*\(", re.IGNORECASE),
    re.compile(r"\bop\.drop_column\s*\(", re.IGNORECASE),
)
_TABLE_PATTERNS = (
    re.compile(r"op\.create_table\(\s*[\"']([^\"']+)[\"']", re.IGNORECASE),
    re.compile(r"CREATE\s+TABLE\s+([a-zA-Z0-9_]+)", re.IGNORECASE),
)


class MigrationBaselineService:
    """Generate deterministic migration baseline records without DB access."""

    def __init__(
        self,
        repository: VersioningRepository,
        policy_adapter: PolicyAdapter,
        *,
        migrations_dir: Path,
        telemetry_service: object | None = None,
        settings: Settings | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._migrations_dir = migrations_dir
        self._telemetry_service = telemetry_service
        self._settings = settings or get_settings()

    def generate(self, schema_version: str, scope: list[str]) -> MigrationBaseline:
        """Generate and persist the migration baseline."""
        self._authorize(
            "migration.baseline.generate",
            scope,
            risk_level="medium",
            context={"schema_version": schema_version},
        )
        files = sorted(path for path in self._migrations_dir.glob("*.py") if path.is_file())
        contents = [(path, path.read_text(encoding="utf-8")) for path in files]
        migration_hash = _migration_hash(contents)
        destructive = _destructive_migrations(contents)
        tables = sorted({table for _, text in contents for table in _extract_tables(text)})
        status = "failed" if destructive else "passed"
        baseline = MigrationBaseline(
            migration_baseline_id=f"migration-baseline-{uuid4().hex}",
            schema_version=schema_version,
            migration_count=len(files),
            migration_hash=migration_hash,
            destructive_migrations=destructive,
            tables=tables,
            status=cast(Any, status),
            report={
                "migration_dir": str(self._migrations_dir),
                "external_calls": False,
                "destructive_override": DESTRUCTIVE_OVERRIDE,
            },
            created_at=datetime.now(UTC),
        )
        saved = self._repository.save_migration_baseline(baseline)
        emit_versioning_telemetry(
            self._telemetry_service,
            event_type="migration_baseline_generated",
            node_type="migration",
            node_id=saved.migration_baseline_id,
            intensity=0.8 if saved.status == "passed" else 1.0,
            scope=scope,
            payload={"schema_version": schema_version, "status": saved.status},
        )
        return saved

    def _authorize(
        self,
        action_type: str,
        scope: list[str],
        *,
        risk_level: str = "low",
        context: dict[str, Any] | None = None,
    ) -> None:
        policy_request = PolicyRequest(
            request_id=f"{action_type}-{uuid4().hex}",
            trace_id=None,
            actor_id=None,
            workspace_id=None,
            action_type=action_type,
            resource_type="migration_baseline",
            resource_id=None,
            risk_level=risk_level,
            approval_present=True,
            requested_permissions=[action_type],
            security_scope=scope,
            context=context or {},
        )
        policy_request = enrich_with_internal_dev_actor(
            policy_request,
            self._settings,
            scope=scope,
            permissions=[action_type],
        )
        decision = self._policy_adapter.authorize(policy_request)
        if not decision.allow:
            raise AIONPolicyDeniedException(decision.reason)


def analyze_migration_files(migrations_dir: Path) -> tuple[list[str], list[str], str]:
    """Return destructive migrations, table names, and deterministic hash."""
    files = sorted(path for path in migrations_dir.glob("*.py") if path.is_file())
    contents = [(path, path.read_text(encoding="utf-8")) for path in files]
    return (
        _destructive_migrations(contents),
        sorted({table for _, text in contents for table in _extract_tables(text)}),
        _migration_hash(contents),
    )


def _migration_hash(contents: list[tuple[Path, str]]) -> str:
    digest = hashlib.sha256()
    for path, text in contents:
        digest.update(path.name.encode())
        digest.update(b"\0")
        digest.update(text.encode())
        digest.update(b"\0")
    return digest.hexdigest()


def _destructive_migrations(contents: list[tuple[Path, str]]) -> list[str]:
    destructive: list[str] = []
    for path, text in contents:
        upgrade_text = text.split("def downgrade", 1)[0]
        if DESTRUCTIVE_OVERRIDE in upgrade_text:
            continue
        if any(pattern.search(upgrade_text) for pattern in _DESTRUCTIVE_PATTERNS):
            destructive.append(path.name)
    return destructive


def _extract_tables(text: str) -> list[str]:
    tables: list[str] = []
    for pattern in _TABLE_PATTERNS:
        tables.extend(pattern.findall(text))
    return tables
