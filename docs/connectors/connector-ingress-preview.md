# Connector Ingress Preview

## Purpose

The connector ingress preview normalizes synthetic inbound connector data while
marking it untrusted. It does not trust connector-returned data.

## Guarantees

Every AION-108 ingress preview returns:

- `trusted=false`
- `provenance_required=true`
- `redaction_applied=true`
- `prompt_injection_scan_required=true`

Response summaries are redacted before output. Ingress preview data cannot
become policy, memory, execution, or activation input without future review
gates.
