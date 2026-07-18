# Self-Improvement Protected Core Boundary

Task: AION-165

## Protected Paths

The protected core includes:

- `.github/workflows/`
- `scripts/*approval*`
- `scripts/*no-go*`
- `scripts/*release*`
- `scripts/lib/*authorization*`
- `services/brain-api/src/aion_brain/policy/`
- `services/brain-api/src/aion_brain/audit/`
- `services/brain-api/src/aion_brain/self_improvement/approval*`
- `services/brain-api/src/aion_brain/self_improvement/protected*`
- `docs/self-improvement/holdout/`
- `docs/self-improvement/policy/`

## Change Requirements

Protected-core changes require a separate proposal, dual approval, security review, full CI, holdout validation, and proof that benchmark or approval controls are not weakened by the same change.

Ordinary improvement proposals may not modify the protected core. A proposal that attempts to change protected policy and its own approval or benchmark controls in the same patch is invalid.

## Runtime Boundary

AION-165 authorizes no runtime self-rewrite, no production deployment, no production canary traffic, no direct write to `main`, no force push, and no automatic merge.
