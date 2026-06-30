# Connector Secret Handling Design

AION-113 permits only redaction preview. It does not persist submitted payloads, does not write secrets, does not materialize secrets, and does not call an external identity provider.

Required handling rules:

- plaintext secret material is never allowed
- browser storage for secret material is never allowed
- logs must contain only redacted placeholders
- audit payloads must store boundary facts, not material
- redaction preview must return a redacted copy only
- raw prompts, hidden reasoning, credentials, provider keys, bearer material, private keys, and OAuth codes are rejected from metadata

The `ConnectorSecretRedactionService` is a preview service. It detects secret-like field names and values, returns `[REDACTED]`, and leaves storage disabled.
