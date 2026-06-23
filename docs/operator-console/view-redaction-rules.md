# Operator Console View Redaction Rules

Operator Console view models must redact unsafe display values before returning
contracts.

## Remove Or Redact

- credential-shaped keys
- provider credential fields
- authorization fields
- source prompt fields
- private reasoning markers
- raw provider payloads
- copyable secret-like values

## Keep

- hashes
- refs
- safe summaries
- statuses
- blockers
- warnings
- timestamps
- owner scope
- audit ids

## Required Statements

- read-only
- no runtime UI
- no raw prompt exposure
- no hidden reasoning exposure
- no secret exposure
- no activation
- no execution

Redaction failures are contract failures. The console does not store removed
values.
