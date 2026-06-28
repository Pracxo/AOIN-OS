# Action Preview Panel

The static Operator Console action preview panel renders dry-run action
records from local demo JSON or future Brain API responses.

The panel shows:

- `action_key`
- `mode`
- expected effects
- blocked effects
- blockers
- review decision
- `execution_allowed=false`
- `external_calls_allowed=false`
- `activation_allowed=false`
- `would_execute=false`

Expected effects describe metadata records that already exist or could be
created by the dry-run flow. Blocked effects describe runtime effects that are
explicitly unavailable.

The panel uses disabled descriptor controls only. It has no runtime write
control and no external fetch target outside localhost.

## AION-097 Authorization Preview

The preview panel is paired with the Action Authorization panel. Authorization
decides whether dry-run preview creation is allowed, then the preview still
renders `would_execute=false`, `execution_allowed=false`,
`activation_allowed=false`, and `external_calls_allowed=false`.
