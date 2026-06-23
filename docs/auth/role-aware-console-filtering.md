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
