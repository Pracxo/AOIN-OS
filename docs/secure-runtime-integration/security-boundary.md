# Secure Runtime Integration Security Boundary

The Secure Runtime Integration boundary is local, operator-invoked, explicit,
and fail-closed. AION-230 authorizes design and validation evidence only.

## Allowed In AION-231

- Offline Ed25519 identity assertion composition using public-key-only registry
  reads.
- Request identity projection before ActorContext construction.
- ActorContext binding after identity verification.
- Persistent replay-protection validation before session activation.
- One explicit local operator session at a time.
- Deterministic capability invocation plans with no actual execution.
- Policy, risk, guardrail, approval-evidence, budget, runtime-guard,
  kill-switch, audit, and observability bindings.
- Read-only operator-console projection of redacted runtime evidence.

## Forbidden In AION-231

- Public authentication endpoints.
- External identity-provider calls.
- Password authentication.
- Credential or token persistence.
- Session token issuance.
- Public-key network retrieval.
- General network access.
- Model-provider calls.
- Connector execution.
- Tool, shell, subprocess, or browser automation execution.
- Module activation or module code loading.
- Dynamic route registration.
- Automatic approval or automatic capability execution.
- Production writes, production memory writes, production policy mutation,
  cognitive-memory writes, belief creation, belief mutation, GLM live execution,
  source rewrite, Git mutation, deployment, model-weight changes, production
  exposure, v0.2 tags, or v0.2 releases.

## Fail-Closed Rule

Every unrecognized identity, session, request, capability, policy, risk,
approval, budget, replay, guard, or kill-switch condition blocks progression.

## AION-232 Closeout

`AION-SRIPE-001` passed. `AION-230-SRI-0001` is closed, consumed by AION-231, expired, and non-reusable. `AION-232-SRI-0002` is active for AION-233 with AION-234 as formal closeout. Provider calls, network egress, credentials, tokens, connectors, tools, production runtime, deployment, model training, v0.2 tags, and v0.2 releases remain disabled.

## AION-234 Closeout

`AION-SRIPE-002` passed all 28 model-gateway operator-evaluation scenarios. `AION-232-SRI-0002` is closed, consumed, expired, and non-reusable. `AION-234-SRI-0003` is active for AION-235 only. AION-235 is authorized to implement a sandboxed deterministic capability and synthetic connector runtime, but no AION-235 source is present in this closeout. Model output remains untrusted and cannot trigger execution. External connectors, real tools, network, credentials, filesystem, process, production runtime, v0.2 tags, and v0.2 releases remain disabled.
