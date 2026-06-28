# ADR 0087: Role-Aware Console View Filtering

## Status

Accepted.

## Decision

AION-096 adds role-aware Operator Console view filtering for local/dev previews. The filter is read-only and uses the local auth role matrix to decide which views, sections, and descriptor-only actions are visible.

Forbidden action descriptors remain visible as safety evidence. No role grants execution, activation, external calls, hard delete, credential storage, production auth enablement, or write authorization.

The static console role switcher is demo-only. It is not login, not logout, not a session issuer, and not a credential prompt.

## Reason

The Operator Console needs role-aware previews before production auth exists. A proof matrix makes future UI filtering testable without adding privileged runtime controls.

## Consequences

Future UI work can filter console views from explicit decisions and audit reports. Production auth remains a later milestone with separate prerequisites.

## Constraints

- No production auth.
- No sessions, tokens, cookies, or credential storage.
- No write authorization.
- No privileged bypass.
- No hidden safety blockers.
- No hiding forbidden actions in sensitive views.
