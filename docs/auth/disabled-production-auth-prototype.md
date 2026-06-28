# Disabled Production Auth Prototype

AION-099 adds a disabled auth runtime contract surface for operator review. It
does not implement production auth, login, logout, provider callbacks,
credential handling, token issuance, cookie issuance, or session persistence.

The prototype exposes three read-only/mock-only API paths:

- `GET /brain/auth-runtime/status`
- `POST /brain/auth-runtime/mock-claims/preview`
- `POST /brain/auth-runtime/audit`

The mock claims preview accepts only `mock.local` or `test.local` issuers and
maps synthetic roles into an actor context preview. The preview is never an
authenticated identity, never stores credentials, never issues tokens or
cookies, and never persists session state.

The status contract always reports production auth and runtime auth as disabled
by default. Blockers remain visible for production auth, external identity,
credentials, token issuance, cookie issuance, session persistence, login, and
logout.

This prototype is a design and verification surface only. It lets operators
inspect future auth runtime shape while preserving the AION-098 architecture
decision that production auth remains disabled.

No external identity provider is integrated. No credentials are stored. No login
endpoint is added.
