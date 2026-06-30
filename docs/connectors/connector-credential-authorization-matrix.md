# Connector Credential Authorization Matrix

AION-113 adds a role-aware credential authorization matrix for preview surfaces only.

Allowed preview/read actions:

- `connector_credentials.boundary.read`
- `connector_credentials.lifecycle.read`
- `connector_credentials.authorization.read`
- `connector_credentials.readiness.preview`
- `connector_credentials.redaction.preview`
- `connector_credentials.status.read`

Denied future actions:

- `connector.credentials.store`
- `connector.credentials.read`
- `connector.credentials.rotate`
- `connector.credentials.revoke`
- `connector.tokens.store`
- `connector.tokens.read`
- `connector.secrets.materialize`
- `connector.oauth.callback`
- `connector.oauth.exchange`
- `connector.oidc.login`
- `connector.saml.assertion`
- `connector.external_identity.bind`

Every matrix row keeps credential access, token access, secret material access, storage, rotation, and revocation disabled today.
