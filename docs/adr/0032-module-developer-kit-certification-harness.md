# ADR 0032: Module Developer Kit and Certification Harness

## Status

Accepted for AION Brain v0.1.

## Decision

AION adds a Module Developer Kit and Capability Certification Harness.

Certification validates module package contracts without executing module code.
The v0.1 scaffold is generic and static only. AION Brain core does not contain
domain modules.

## Reason

Future modules need a safe plug-in path before runtime registration. AION must
validate schemas, risk, permissions, memory scopes, policy, autonomy, dry-run
behavior, and audit metadata before trusting a module package.

## Consequences

AION can reject unsafe modules before runtime registration. Certification
records become auditable Brain-owned artifacts. Future runtime adapters can rely
on certified package metadata.

## Constraints

- No external calls.
- No module code execution.
- No provider SDK coupling.
- No vertical module logic in Brain core.

