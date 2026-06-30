# Connector Credential Redaction And Logging

AION-113 requires connector credential logs to prove absence, denial, and redaction decisions only. Logs must not include credential material, token material, provider keys, external identity assertions, OAuth codes, raw prompts, or hidden reasoning.

Redaction preview records:

- redaction id
- whether redaction was applied
- detected field categories
- redacted payload copy
- blocked field paths
- storage/access flags set to false

Audit and visual telemetry records must use the same boundary facts: storage disabled, token storage disabled, material absent, and connector runtime credential access disabled.
