# Operator Data Safety

AION-087 defines data safety rules for a future Operator Console. It does not
add a runtime UI.

## Sensitive categories

- raw prompts
- hidden reasoning
- chain-of-thought
- provider credentials
- API keys
- secrets
- raw model payloads
- untrusted retrieved context
- raw extension manifests with suspicious fields
- audit details with secret-like values

## Display rules

- Display summaries, hashes, refs, status, blockers, warnings, owner scope,
  timestamps, policy reasons, and audit ids.
- Never display raw secrets.
- Never display hidden reasoning.
- Never display raw prompts.
- Never expose provider credentials.
- Never allow copyable secret fields.
- Never mark untrusted context as trusted.
- Redact secret-like keys before rendering or export.
- Prefer refs and hashes over raw payloads.

## Review handling

If a future view cannot prove redaction, it must show a blocker instead of the
unsafe field. Operators should see enough context to decide what gate failed,
not enough context to recover a secret or private reasoning trace.

## AION-088 API contract safety

AION-088 enforces redaction at the contract layer before any runtime UI exists.
The console audit checks examples and docs for no raw prompt exposure, no
hidden reasoning exposure, and no secret exposure.

View models remain read-only. They allow no activation and no execution.
