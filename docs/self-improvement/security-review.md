# Self-Improvement Security Review

AION-175 preserves a fail-closed security posture for the self-improvement platform.

## Security Controls

- Direct writes to `main` remain rejected.
- Self-approval remains prohibited.
- Automatic merge remains disabled.
- Production deployment remains disabled.
- Production canary and production exposure remain disabled.
- Runtime self-rewrite remains disabled.
- Model-weight training remains disabled.
- Protected-core ordinary modification remains blocked.
- Holdout benchmark mutation through candidate code remains blocked.
- Test weakening remains detected and disallowed unless a separate elevated approval exists.
- Approval invalidates when the approved commit, diff hash, benchmark fingerprint, rollback commit, or deployment scope changes.

## Evidence Boundaries

The governance and readiness ledgers are synthetic, read-only evidence. They do not store credentials, tokens, private data, internal rationale, source generation transcripts, or private operator material.

## Residual Risk

Future activation would create new risk in runtime exposure, model-backed patch generation, provider integrations, production deployment, and long-term preference storage. Those are explicitly outside AION-175 and require a new authorization, security review, rollback plan, holdout validation, and full CI.
