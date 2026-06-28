# Credential Handling No-Go Rules

These rules block production auth implementation or release.

- No plain text credentials.
- No API keys in repo.
- No provider secrets in examples.
- No browser localStorage secrets.
- No session token in docs.
- No hardcoded tokens.
- No provider calls without release gate.
- No auth bypass.
- No login/logout route before release gate.
- No credential, token, cookie, or session persistence before approved storage
  design.
- No raw provider payloads in logs, telemetry, docs, audit records, or public
  Brain contracts.
- No reverse proxy identity header trust without spoofing controls.
- No role mapping that bypasses ActorContext, policy, audit, role matrix, or
  dry-run action authorization.

AION-098 adds these rules only. It adds no production auth runtime, no provider
integration, no credentials, no tokens, no sessions, and no cookies.
