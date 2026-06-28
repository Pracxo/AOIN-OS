# Session Safety Audit

The local session audit is a deterministic local check. It inspects the
AION-095 no-go conditions without calling external services.

The audit checks for:

- no login or logout endpoint
- no credential storage
- no token issuance
- no cookie issuance
- no session persistence
- no production auth
- safe examples
- no AION-095 migration
- no frontend dependency files
- no static console login form

The audit records only metadata and safety status. It does not store passwords,
credentials, bearer material, cookies, raw prompts, hidden reasoning, or session
state.

## AION-097 Authorization Audit

Action authorization audit reuses the session boundary proof. It confirms that
dry-run authorization blocks writes, execution, activation, external calls, and
unsafe session contexts before any preview or review record is allowed.
