# Known Limitations

The AION-175 platform is intentionally implemented but disabled.

## Current Limits

- Production runtime self-improvement is not enabled.
- Production source rewrite is not enabled.
- Production canary exposure is not enabled.
- Model-backed patch generation is not enabled by default.
- GitHub operations remain adapter-driven and must be explicitly configured.
- Adaptive-learning outputs are data-only candidates and do not activate runtime behavior directly.
- Preference learning is user-scoped and reversible, but high-impact preference changes still require approval.
- Procedural skill evolution records data-only steps and cannot generate executable source.
- Model-weight training is not part of this platform.

## Required Future Work Before Activation

Any future activation requires a new authorization, exact approval record, full security review, rollback plan, production observability plan, protected-core review where applicable, holdout validation, full CI, and explicit operator acceptance.
