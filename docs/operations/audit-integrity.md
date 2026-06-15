# Audit Integrity Operations

AION v0.1 audit integrity is a local tamper-evident audit and provenance layer.
It records important Brain actions as append-only entries, links entries with a
sha256 hash chain, and lets operators verify whether the local chain is intact.

It is not a compliance certification system, cloud audit drain, or external
notarization service.

## Model

- `AuditEntry` is the append-only record of what happened.
- `payload_hash` hashes the canonical, redacted payload.
- `previous_hash` points to the prior entry.
- `entry_hash` hashes the previous hash, payload hash, sequence number, and metadata.
- `AuditIntegrityCheckpoint` records a local root hash over a contiguous entry range.
- `ProvenanceLink` connects generic AION records such as events, commands, policy decisions, approvals, model calls, backups, and release packages.
- `AuditVerificationRun` reports sequence, payload hash, entry hash, and checkpoint integrity.
- `AuditExportRecord` records local JSON/JSONL exports.

## Append-Only Rule

Audit entries are never hard-deleted. Corrections are represented by appending a
new correction, redaction marker, or provenance update. Provenance links can be
soft-deleted by setting `deleted_at`; the original row remains present.

## Redaction

Audit payloads are redacted before hashing and storage. Sensitive keys such as
passwords, tokens, API keys, raw prompts, authorization headers, and credentials
are replaced with `[REDACTED]`. Chain-of-thought and hidden reasoning fields are
removed entirely.

## Verification

Use:

```bash
./scripts/audit-verify.sh
```

or:

```bash
./scripts/aionctl.sh --scope workspace:main audit verify
```

Verification checks contiguous sequence numbers, previous hash links, payload
hashes, entry hashes, checkpoint roots, and checkpoint chaining.

## Export

Exports are local only:

```bash
./scripts/audit-export.sh
./scripts/aionctl.sh --scope workspace:main audit export --write
```

The default export path is `artifacts/audit`, which is ignored by git.

## Limits

- No external anchoring in v0.1.
- No external SIEM or cloud logging.
- No raw secrets.
- No raw prompts.
- No chain-of-thought storage.
- No domain-specific audit logic.
