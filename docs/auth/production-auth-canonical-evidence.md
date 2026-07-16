# Production Auth Canonical Evidence

AION-154 adds deterministic evidence serialization for the disabled
production-auth core.

Version identifiers:

- `schema_version=production-auth-core/v1`
- `canonicalization_version=production-auth-canonical-json/v1`
- `policy_version=production-auth-policy/v1`
- `reason_code_registry_version=production-auth-reason-codes/v1`

Canonical serialization uses only the Python standard library:

- UTF-8 output
- sorted object keys
- compact separators
- UTC-normalized datetime values
- no memory-address representations
- no caller-owned data mutation
- no NaN, infinity, non-string object keys, or unsupported values

Evidence fingerprints are SHA-256 hashes of canonical payloads. The fingerprint
field is excluded from its own hash. Fingerprints are present on:

- `ProductionAuthCoreStatus`
- `ProductionAuthPolicyDecision`
- `ProductionAuthAuditEvent`
- `ProductionAuthProvenanceRecord`
- `ProductionAuthDiagnosticSnapshot`

Reason codes are centralized in `aion_brain.production_auth.reason_codes`.
Unknown or duplicate reason codes fail closed, and accepted reason collections
are normalized to registry order.

The canonical evidence layer never stores credentials, tokens, cookies, raw
identity-provider payloads, raw prompts, hidden reasoning, or protected material.
