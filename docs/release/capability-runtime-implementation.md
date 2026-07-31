# Capability Runtime Implementation

AION-235 implements the AION-234-SRI-0003 scoped sandboxed deterministic capability runtime. The runtime accepts only explicit authenticated operator capability selections, validates transient input against restricted schemas, builds deterministic execution plans, binds policy, risk, guardrails and pre-existing approvals where required, enforces zero-external-effect budgets, checks the parent kill switch, admits the request into an in-memory sandbox, and dispatches through a static closed map.

The closed runtime operations are health read, observability read, audit summary read, text normalization, SHA-256 hashing, restricted JSON validation, synthetic reference connector read simulation, and synthetic reference connector write preview. The synthetic connector uses only an injected in-memory fixture registry. The write-preview operation creates deterministic before, proposed-after and preview fingerprints and applies no mutation.

Model output remains proposal material only. It cannot select a capability, create a plan, satisfy approval, trigger dispatch, authorize a connector, authorize a tool, bypass policy, risk, guardrails, budgets or the kill switch, or become production action authority.

AION-234-SRI-0003 remains active and non-reusable pending AION-236 evaluation and closeout. AION-237 remains unauthorized. v0.2 remains unreleased.
