# Shadow-Mode Boundary

AION-177 permits a future AION-178 implementation to build a shadow-mode
observation path. The boundary is strict:

- Repository inspection is read-only.
- Runtime execution is offline and deterministic.
- Observations use synthetic or redacted inputs only.
- Outputs are advisory review items only.
- Operator review is required before any future action.

Forbidden behavior:

- Source mutation.
- Git write.
- Branch creation.
- Pull request creation.
- Approval creation.
- Automatic merge.
- Production canary.
- Production deployment.
- External provider calls.
- Connector runtime calls.
- Network calls.
- Protected-core bypass.
- v0.2 tag or release creation.
- `aion-v0.1.0` tag movement.

The AION-177 authorization is non-reusable and scoped to AION-178. Completion of
AION-178 must consume or close this transaction before any later activation
request can be considered.
## AION-178 Boundary Update

AION-178 may create only review-bound shadow evidence: observations,
evaluation summaries, repeated failure-pattern candidates, bounded hypotheses,
regression-test specifications, shadow proposal candidates, operator review
items, audit, provenance, diagnostics, and budget records. Source mutation, Git
write, pull request creation, approval creation, automatic merge, production
canary, production deployment, external provider calls, connector runtime
calls, runtime influence, promotion, and v0.2 tag or release creation remain
out of scope.
