# Connector Token Lifecycle

AION-113 does not create a connector token lifecycle runtime. Token storage, token read paths, refresh paths, exchange paths, and external identity callbacks remain disabled.

Future token handling cannot start until:

- the credential store architecture is approved
- production auth exists
- external identity runtime is explicitly enabled by a later milestone
- audit/provenance records can link token lifecycle actions to an operator decision
- rotation and revocation behavior is tested

The current contract keeps `token_storage_enabled=false`, `token_storage_allowed=false`, and `token_access_allowed=false`.
