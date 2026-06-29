# Connector Simulation Safety

Connector simulation safety is enforced in contracts, service wiring, policy
catalog entries, diagnostics, hardening checks, freeze checks, release package
summaries, SDK commands, and static console evidence.

Blocked material:

- endpoint-like fields
- credential-like fields
- token-like fields
- raw prompt material
- hidden reasoning material
- external address strings
- secret-like markers

Simulator findings are safe summaries. They do not expose blocked values and do
not trust connector ingress.

No-go boundaries:

- no connector runtime enablement
- no route registration
- no connector/provider SDK dependency
- no external egress
- no credential or token storage
- no tool execution
- no write execution
- no hard delete
