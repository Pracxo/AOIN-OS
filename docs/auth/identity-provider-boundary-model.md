# Identity Provider Boundary Model

## Trusted Identity Provider Boundary

The provider may be trusted to authenticate the human operator only after AION
has selected and configured that provider through a release gate. AION must
verify issuer, audience, signature, expiry, nonce/state, revocation posture, and
claim mapping before any provider assertion affects ActorContext.

## AION Backend Boundary

The backend is responsible for translating verified identity assertions into
AION-owned actor, workspace, role, scope, policy, audit, and action
authorization inputs. The backend must not trust browser state, raw headers, or
unverified proxy claims.

## Operator Console Boundary

The console may display authenticated state in a future implementation, but it
must not become the source of identity truth. It must not store credentials,
token values, cookie values, provider payloads, or session material.

## Reverse Proxy Boundary

Reverse proxy auth is optional later. AION may trust it only when the proxy is
part of the deployment boundary, strips inbound identity headers, injects
verifiable identity evidence, and prevents spoofing from untrusted clients.

## API Boundary

Brain APIs must require validated actor context and policy authorization.
Production auth must not add routes that bypass existing policy, audit, role
matrix, or dry-run action authorization controls.

## Audit Boundary

Audit may trust only AION-generated correlation data and verified provider
subject references. It must not store credentials, token values, cookie values,
raw provider payloads, or raw headers.

## What Each Layer May Trust

| Layer | May Trust |
| --- | --- |
| Provider | its own authentication ceremony and account lifecycle |
| Reverse proxy | upstream identity only after deployment hardening |
| AION backend | validated identity assertions and configured role mappings |
| Operator Console | redacted auth status returned by AION APIs |
| Policy | AION-owned ActorContext, scope, roles, and request metadata |
| Audit | AION-generated trace ids and redacted auth decision metadata |

## What Each Layer Must Verify

| Layer | Must Verify |
| --- | --- |
| Provider | account status, MFA posture, and revocation |
| Reverse proxy | trusted upstream, stripped inbound headers, TLS posture |
| AION backend | issuer, audience, expiry, signature, role mapping, scope |
| Operator Console | local origin constraints and redaction before display |
| Policy | requested action, scope, actor, risk, and constraints |
| Audit | trace correlation and absence of protected material |
