# Connector Credential No-Go

AION-113 blocks connector credential implementation work.

No-go conditions:

- credential storage path added
- token storage path added
- plaintext secret path added
- browser secret storage added
- credential or token read command added
- rotate or revoke command added
- OAuth/OIDC/SAML runtime added
- external identity binding added
- connector runtime credential access enabled
- external call path added
- package dependency added
- migration added

`scripts/connector-credential-no-go-regression.sh` enforces this boundary.
