# Connector Credential Boundary

## Purpose

This boundary keeps connector credentials and tokens absent from AION-106. It
defines the future requirements before any connector credential integration can
be proposed.

## Current Boundary

- no credentials in repo
- no credentials in examples
- no credentials in static console
- no browser localStorage secrets
- no plain text secrets
- no provider tokens in logs
- no OAuth, SAML, OIDC, LDAP, AD, Passkey, WebAuthn, cloud IAM, or external identity runtime
- no login/logout behavior
- no token issuance
- no cookie issuance
- no session persistence

## Future Secret Store Requirements

Future connector work must define a secret store that keeps secret material
outside AION Brain. Brain records may hold metadata-only references, status,
rotation timestamps, revocation status, and redacted audit references.

## Rotation Model

Future rotation must record requested actor, connector reference, credential
reference, rotation reason, policy decision, operator decision, previous
metadata version, new metadata version, and redacted provenance. Rotation must
not reveal secret values.

## Revocation Model

Future revocation must disable future connector use, preserve audit records,
mark dependent connector capabilities unavailable, and avoid hard delete.

## Audit Model

Future credential audit must record metadata-only events for create, rotate,
revoke, read-reference, policy denial, operator denial, and release-gate
failure. Logs must never include credential values, bearer tokens, cookies,
passwords, provider secrets, raw headers, or raw provider payloads.

## No-Go Conditions

- credential material appears in repository files
- credential material appears in examples
- credential material appears in static console data
- localStorage or sessionStorage stores secrets
- token storage is added
- provider tokens appear in logs
- credential values appear in audit records
- external identity runtime is added
- login/logout behavior is added
## AION-108 Disabled Prototype Relationship

AION-108 keeps connector credential handling disabled. Mock manifests must set
`credentials_required=false`, examples contain no credential material, and the
static console exposes no connector credential input.

## AION-109 Review Gate Relationship

AION-109 adds the credential/token absence proof. It confirms connector
credentials, token storage, provider SDKs, secret storage, migrations, and
external identity runtime remain absent before future design-only credential
architecture work.
