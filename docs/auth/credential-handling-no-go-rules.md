# Credential Handling No-Go Rules

These rules block production auth implementation or release.

AION-099 follows these no-go rules. Mock claims are synthetic preview fixtures,
not credentials, and must never be stored or accepted as production identity
material.

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

## Connector Credential Boundary

AION-106 extends the credential no-go posture to future external connectors.
Connector credentials and tokens remain absent from the repository, examples,
static console data, logs, telemetry, audit records, and public Brain
contracts.

Future connector credential work requires a secret-store design, rotation
model, revocation model, audit model, policy gate, operator review, and release
gate. Connector metadata must not contain credential values, browser storage
must not hold connector secrets, and connector examples must remain synthetic.
