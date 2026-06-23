# Provider Readiness Gate

The provider readiness gate assesses whether provider metadata has passed the
local safety checks required for future provider enablement work.

It checks:

- prompt egress guard presence
- model output governance requirement
- tool intent blocking requirement
- grounding requirement
- policy readiness
- audit readiness
- external model calls disabled
- provider credentials disabled

Readiness can report `metadata_only`, `dry_run_ready`, or `blocked`. It never
sets provider runtime state and never enables external calls or credentials.

