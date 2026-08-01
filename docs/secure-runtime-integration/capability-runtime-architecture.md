# Capability Runtime Implementation

AION-235 implements the AION-234-SRI-0003 scoped sandboxed deterministic capability runtime. The runtime accepts only explicit authenticated operator capability selections, validates transient input against restricted schemas, builds deterministic execution plans, binds policy, risk, guardrails and pre-existing approvals where required, enforces zero-external-effect budgets, checks the parent kill switch, admits the request into an in-memory sandbox, and dispatches through a static closed map.

The closed runtime operations are health read, observability read, audit summary read, text normalization, SHA-256 hashing, restricted JSON validation, synthetic reference connector read simulation, and synthetic reference connector write preview. The synthetic connector uses only an injected in-memory fixture registry. The write-preview operation creates deterministic before, proposed-after and preview fingerprints and applies no mutation.

Model output remains proposal material only. It cannot select a capability, create a plan, satisfy approval, trigger dispatch, authorize a connector, authorize a tool, bypass policy, risk, guardrails, budgets or the kill switch, or become production action authority.

AION-234-SRI-0003 remains active and non-reusable pending AION-236 evaluation and closeout. AION-237 remains unauthorized. v0.2 remains unreleased.

## AION-236 Secure Runtime Integration Status

AION-SRIPE-003 passed with report fingerprint `61e50ce0829e85b27b61a7620bb1ca4a7f58ad0c6f8cad0b93f0250c89365a11`. `AION-234-SRI-0003` is closed and consumed by AION-235. `AION-236-SRI-0004` is active for AION-237. AION-237 is authorized but not implemented. Public listening, external egress, browser persistence, provider calls, external connectors, real tools, production writes, deployment, model training and v0.2 release readiness remain disabled.
