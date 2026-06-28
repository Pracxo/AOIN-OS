# Mock Claims Adapter

The mock claims adapter is a local preview adapter. It accepts synthetic claims
and returns a role-aware actor context preview without authenticating the
subject.

Allowed issuer values:

- `mock.local`
- `test.local`

Allowed roles are the local auth roles already used by the Operator Console:
`viewer`, `operator`, `reviewer`, `admin`, `auditor`, and `system_service`.

The adapter rejects secret-like keys and values in claims and metadata. It does
not accept credentials, tokens, cookies, session identifiers, provider payloads,
raw prompts, or hidden reasoning text.

The output is marked `preview_only=true`, `production_identity=false`,
`credentials_present=false`, `token_present=false`, `cookie_present=false`, and
`session_persisted=false`.
