# Local Backup and Restore Preview

AION v0.1 backup is local and application-level. Restore apply is disabled by default.

The backup layer exports AION Brain records through service-owned resource
readers. It does not call `pg_dump`, restore raw database snapshots, upload to
cloud storage, or call external services.

## Export

Dry-run export records the job and planned resource files without writing a
backup directory:

```bash
./scripts/aionctl.sh --scope workspace:main backups export
```

Write mode creates `manifest.json`, `checksums.json`, `validation.json`, and
`resources/*.jsonl` under `artifacts/backups/<backup_id>/`:

```bash
./scripts/aionctl.sh --scope workspace:main backups export --write
./scripts/backup-local.sh
```

The default redaction mode is `redact_sensitive`. Use `metadata_only` for a
minimal portability record, or `exclude_sensitive` when sensitive-looking
records should be skipped entirely.

## Validate

Validate a stored backup job:

```bash
./scripts/aionctl.sh --scope workspace:main backups validate --id <backup_job_id>
```

Validate a local backup path:

```bash
./scripts/aionctl.sh --scope workspace:main backups validate --path artifacts/backups/<backup_id>
```

Validation checks manifest shape, resource JSONL parsing, file checksums, root
checksum, owner scope, supported resources, unsafe files, and raw secret-like
values.

## Restore Preview

Restore preview is the supported v0.1 restore operation:

```bash
./scripts/aionctl.sh --scope workspace:main restore preview --backup-path artifacts/backups/<backup_id>
./scripts/restore-preview.sh artifacts/backups/<backup_id>
```

Preview detects existing IDs, missing dependencies, scope mismatches, version
mismatches, unsupported resources, checksum mismatches, and sensitive data that
is not restorable by default.

## Restore Apply

`POST /brain/restore/apply` records a dry-run restore job by default. Apply mode
requires approval and is disabled by `AION_BACKUP_RESTORE_APPLY_ENABLED=false`
in v0.1. No direct database restore occurs.

## Files

Backup artifacts are ignored by git through `artifacts/backups/`. Do not commit
backup outputs, `.env` files, raw headers, cache directories, virtualenvs, local
object stores, or local vector indexes.
