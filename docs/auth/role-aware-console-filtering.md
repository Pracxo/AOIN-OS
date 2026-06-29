# Role-Aware Console Filtering

Role-aware console filtering narrows read-only Operator Console view models for local development.

Filtering uses a synthetic `LocalAuthContext` and never mutates source records. It can remove unreadable sections and allowed action descriptors that the local role cannot request. Forbidden action descriptors remain visible so operators can see blocked capabilities and no-go reasons.

Role behavior:

- `viewer` can read views only
- `operator` can request descriptor-only dry-run actions
- `reviewer` can create review records
- `admin` is reserved for future design-level settings and grants no write behavior in AION-094
- `auditor` can read audit and provenance-oriented views
- `system_service` is synthetic and non-privileged

The filter always applies redaction and returns `read_only=true`.

## AION-095 Session Context

Role-aware console filtering may accept `LocalSessionContext` metadata and map
it back to the same non-privileged local auth role matrix. Session context never
adds write, execution, activation, or external-call grants.

## AION-096 Strengthening

Role-aware filtering now has a permission proof matrix, fail-closed decisions,
section-level filtering, action descriptor filtering, and role access audit
reports. Forbidden action descriptors and safety blockers remain visible after
filtering.

## AION-097 Action Authorization Use

Role filtering remains visibility-only. Dry-run action authorization uses the
same role proof matrix for request, preview, and review authorization, but it
does not grant execute, activation, write, external-call, login, or credential
capability.
## AION-104 Prototype Review Gate

AION-104 keeps role-aware console filtering as visibility-only. Role filtering
may hide or mark read-only sections, but forbidden actions and safety blockers
remain visible. No role grants production auth, writes, activation, execution,
external calls, credential handling, token issuance, cookie issuance, session
persistence, or privileged bypass.
