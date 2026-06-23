# Provider Safety Boundaries

AION model provider hardening has strict v0.1 boundaries:

- no provider SDKs
- no provider endpoints
- no API keys
- no credential storage
- no external network calls
- no prompt transmission
- no raw prompt persistence
- no hidden reasoning persistence
- no model invocation
- no tool execution
- no provider activation

Future provider work must pass prompt governance, model input manifest checks,
provider readiness, prompt egress guard, model output governance, tool intent
blocking, grounding, audit/provenance, and operator review.

