# v0.2 Candidate Workstream Map

## Purpose

This map lists candidate v0.2 workstreams for planning. Each workstream is
planning-only and implementation-unapproved.

## Workstreams

| Workstream | Planning Status | Implementation Approval | Planning Output |
| --- | --- | --- | --- |
| production auth implementation planning | planning-only | unapproved | ADR candidate, threat model, credential/session boundary, rollback and audit plan |
| connector runtime implementation planning | planning-only | unapproved | ADR candidate, runtime boundary, egress/ingress guard plan, policy and audit model |
| credential store implementation planning | planning-only | unapproved | ADR candidate, protected-material lifecycle, redaction, rotation, revocation, audit model |
| sandbox runtime implementation planning | planning-only | unapproved | ADR candidate, isolation model, filesystem/network/process limits, failure model |
| operator write execution planning | planning-only | unapproved | ADR candidate, separation-of-duties model, dry-run to write transition, rollback path |
| module activation implementation planning | planning-only | unapproved | ADR candidate, code loading boundary, package trust, runtime registration guard |
| external call release gate planning | planning-only | unapproved | ADR candidate, egress allowlist model, redaction, policy enforcement, rollback model |
| audit/provenance hardening | planning-only | unapproved | ADR candidate, append-only event model, evidence links, redaction validation |
| rollback and recovery model | planning-only | unapproved | ADR candidate, disable path, recovery records, operator review flow |
| static console to production UI decision | planning-only | unapproved | ADR candidate, UI boundary, auth dependency, route dependency, no-build exit criteria |

## Shared Blockers

Every workstream remains blocked from implementation until a future task adds
an explicit ADR, scoped gates, no-go regression, operator review evidence,
rollback evidence, policy enforcement evidence, and full repository checks.

## Planning-Only State

This map does not create a v0.2 tag, create a release, enable runtime code,
approve implementation, call external services, store protected material, or
enable sandbox execution.
