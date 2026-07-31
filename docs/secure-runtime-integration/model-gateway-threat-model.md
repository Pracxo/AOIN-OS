# Model Gateway Threat Model

Threats documented for AION-233:

- provider spoofing
- model-ID substitution
- manifest tampering
- prompt injection
- system-instruction override
- context poisoning
- secret exfiltration
- credential leakage
- prompt retention
- response retention
- hidden-reasoning retention
- cross-session context leakage
- token-budget evasion
- context-budget evasion
- retry storms
- fallback downgrade
- circuit-breaker bypass
- cost-budget evasion
- latency-budget evasion
- schema escape
- structured-output smuggling
- tool-call smuggling
- function-call smuggling
- executable-content injection
- model output treated as truth
- model output treated as approval
- model output written to memory
- model output mutating belief
- model output mutating policy
- model output triggering connectors
- model output triggering tools
- provider raw-payload retention
- provider network egress
- production-route exposure
- source rewrite
- Git mutation
- deployment
- model training

Core rule: a model gateway may prepare, route, simulate, validate, classify, and attest a model request and response. It may not call a live provider under AION-232-SRI-0002.
