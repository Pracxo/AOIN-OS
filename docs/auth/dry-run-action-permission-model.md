# Dry-Run Action Permission Model

AION-097 connects local auth roles to governed operator action authorization.

Role behavior:

- `operator` can request dry-run preview authorization.
- `reviewer` can request review record authorization.
- `viewer` cannot request dry-run operator action authorization.
- `auditor` cannot request dry-run operator action authorization.
- unknown roles fail closed.

The role matrix is advisory proof for local development only. It is not
production auth, does not store credentials, and does not create sessions.

Every authorization decision keeps:

- `write_allowed=false`
- `execution_allowed=false`
- `activation_allowed=false`
- `external_calls_allowed=false`
