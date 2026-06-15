# Migration Runbook

## Purpose

Migrations document local database schema changes for AION Brain services.

## Creating A Migration

1. Add a new numbered file under `infra/postgres/migrations`.
2. Define tables and indexes with SQLAlchemy metadata.
3. Keep names unique and descriptive.
4. Do not connect to a database from migration checks.

## Inspection

Run:

```bash
scripts/migration-check.sh
```

The check verifies non-empty files, unique names, duplicate table definitions
within one file, and destructive operations.

## Destructive Migration Rule

`DROP TABLE` is not allowed unless the migration includes the explicit comment:

```text
AION_ALLOW_DESTRUCTIVE_MIGRATION
```

## Rollback Policy

Rollback is a placeholder for a later task. For v0.1, prefer additive
migrations and local data recreation when needed.
